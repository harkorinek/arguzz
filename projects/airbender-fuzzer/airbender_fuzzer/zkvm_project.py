import io
import logging
import os
import shutil
from pathlib import Path

from circil.ir.node import Circuit
from circil.ir.type import IRType
from zkvm_fuzzer_utils.file import create_file, replace_in_file
from zkvm_fuzzer_utils.project import AbstractCircuitProjectGenerator
from zkvm_fuzzer_utils.rust.common import (
    ir_type_to_str,
    stream_circuit_output_and_compare_routine,
)
from zkvm_fuzzer_utils.rust.ir2rust import CircIL2UnsafeRustEmitter

from airbender_fuzzer.settings import (
    RUST_GUEST_CORRECT_VALUE,
    RUST_GUEST_RETURN_TYPE,
    # get_rust_toolchain_version,
)

logger = logging.getLogger("fuzzer")


def indent_line(n, line):
    if not line or line.isspace():
        return line
    else:
        return " " * n + line.lstrip()


def join_lines_with_indent(n, lines):
    return "\n".join(map(lambda line: indent_line(n, line), lines))


# ---------------------------------------------------------------------------- #
#                                Circuit Project                               #
# ---------------------------------------------------------------------------- #


class CircuitProjectGenerator(AbstractCircuitProjectGenerator):
    commit_or_branch: str
    cached_patch_crates_io: str | None  # TODO: needed or not?
    template_source_dir: str

    def __init__(
        self,
        root: Path,
        zkvm_path: Path,
        circuits: list[Circuit],
        fault_injection: bool,
        trace_collection: bool,
        commit_or_branch: str,
    ):
        super().__init__(root, zkvm_path, circuits, fault_injection, trace_collection)
        self.cached_patch_crates_io = None
        self.commit_or_branch = commit_or_branch
        self.template_source_dir = root / ".." / ".." / "zkvm-fuzzing" / \
            "projects" / "airbender-fuzzer" / "host"

    @property
    def patch_crates_io_section(self) -> str:
        if self.cached_patch_crates_io is None:
            cargo_toml_lines = (
                self.zkvm_path / "Cargo.toml").read_text().split("\n")
            patch_section_lines = []
            is_record = False
            for line in cargo_toml_lines:
                if line == "[patch.crates-io]":
                    is_record = True
                if line == "":
                    is_record = False
                if is_record:
                    patch_section_lines.append(line)
            self.cached_patch_crates_io = "\n".join(patch_section_lines)

        assert self.cached_patch_crates_io, "singleton was not set!"
        return self.cached_patch_crates_io

    def create(self):
        if os.path.isdir(self.root) and os.listdir(self.root):
            shutil.copytree(self.template_source_dir / "src",
                            self.root / "src", dirs_exist_ok=True)
            shutil.copytree(self.template_source_dir / "guest",
                            self.root / "guest", dirs_exist_ok=True)
        else:
            shutil.copytree(self.template_source_dir,
                            self.root, dirs_exist_ok=True)

        self.patch_host_main_rs()
        self.patch_guest_main_rs()
        self.create_guest_lib_rs()

    def patch_host_main_rs(self):
        replace_in_file(
            self.root / "src" / "main.rs",
            list({
                "{{ arguzz_cli_args }}":
                    "\n".join(
                        "\n"
                        "    #[clap(long)]\n"
                        f"    {e.name}: {ir_type_to_str(e.ty_hint)},"
                        for e in self.circuit_candidate.inputs
                    ),

                 "{{ arguzz_circuit_inputs }}":
                    "\n".join(
                        f"        args.{e.name} as u32,"
                        for e in self.circuit_candidate.inputs
                    ),
                 }.items())
        )

    def patch_guest_main_rs(self):
        replace_in_file(
            self.root / "guest" / "src" / "main.rs",
            list({
                "{{ arguzz_n_inputs }}":
                    str(len(self.circuit_candidate.inputs)),

                "{{ arguzz_input_args }}":
                    "\n".join(
                        "            circuit_inputs.clone(),"
                        for _ in range(len(self.circuits))
                    ),
            }.items()),
        )

    def create_guest_lib_rs(self):

        buffer = io.StringIO()

        buffer.write('#![no_std]\n')
        # buffer.write("#![allow(unconditional_panic)]\n")
        buffer.write("#![allow(arithmetic_overflow)]\n")

        # # NOTE: it is unclear to me why we need this as the program
        # #       is compiled to riscv and not x86, but the warning says
        # #       stuff about sub registers for x86.
        # buffer.write("#![allow(asm_sub_register)]\n\n")

        for circuit in self.circuits:
            buffer.write(CircIL2UnsafeRustEmitter().run(circuit))
            buffer.write("\n")
        buffer.write("\n")

        buffer.write("pub fn circuits(\n")
        input_arr_type = f"[u32; {len(self.circuit_candidate.inputs)}]"
        for circuit in self.circuits:
            buffer.write(f"    {circuit.name}_args: {input_arr_type},\n")
        buffer.write(f") -> {RUST_GUEST_RETURN_TYPE} {{\n")

        buffer.write("\n")
        buffer.write("    //\n")
        buffer.write("    // Parse Inputs and call Circuits\n")
        buffer.write("    //\n\n")

        for circuit in self.circuits:
            buffer.write(f"    // -- {circuit.name} --\n")
            for idx, circuit_input in enumerate(circuit.inputs):
                in_var = f"{circuit.name}_{circuit_input.name}"
                ir_type = ir_type_to_str(circuit_input.ty_hint)
                arg_access = f"{circuit.name}_args[{idx}]"
                if circuit_input.ty_hint == IRType.Bool:
                    buffer.write(f"    let {in_var}: {ir_type} ="
                                 f"{arg_access} == 0_u32;\n")
                else:
                    buffer.write(f"    let {in_var}:"
                                 f"{ir_type} = {arg_access};\n")
            buffer.write("\n")

        def helper_commit_and_exit(value: int, is_end: bool) -> list[str]:
            if is_end:
                return [f"{value}_u32"]
            else:
                return [f"return {value}_u32;"]

        stream_circuit_output_and_compare_routine(
            buffer,
            self.circuits,
            RUST_GUEST_CORRECT_VALUE,
            helper_commit_and_exit,
        )

        buffer.write("}\n")

        create_file(self.root / "guest" / "src" / "lib.rs", buffer.getvalue())

    # ---------------------------------------------------------------------------- #
