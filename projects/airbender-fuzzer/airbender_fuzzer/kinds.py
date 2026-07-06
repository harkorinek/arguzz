from enum import StrEnum

# TODO?: add other kinds

class InstrKind(StrEnum):
    # TODO: add instructions, e.g.:
    # ADD = "add"

    @classmethod
    def computations(cls) -> list["InstrKind"]:
        return [
            # TODO: add above instructions, e.g.:
            # cls.ADD,
        ]

    @classmethod
    def loads(cls) -> list["InstrKind"]:
        return [] # TODO: add instructions

    @classmethod
    def is_load(cls, kind: "InstrKind") -> bool:
        return kind in cls.loads()

    @classmethod
    def stores(cls) -> list["InstrKind"]:
        return [] # TODO: add instructions

    @classmethod
    def is_store(cls, kind: "InstrKind") -> bool:
        return kind in cls.stores()

    @classmethod
    def is_computation(cls, kind: "InstrKind") -> bool:
        return kind in cls.computations()

    @classmethod
    def branches(cls) -> list["InstrKind"]:
        return [] # TODO: add instructions

    @classmethod
    def is_branch(cls, kind: "InstrKind") -> bool:
        return kind in cls.branches()


class InjectionKind(StrEnum):
    # Modifies the loaded word from the program memory.
    INSTR_WORD_MOD = "INSTR_WORD_MOD"

    @classmethod
    def retrieve_injection_types(
        cls, kind: InstrKind, enabled: list["InjectionKind"]
    ) -> list["InjectionKind"]:
        # following types are always valid
        result = {
            cls.INSTR_WORD_MOD,
        }

        return sorted(list(result.intersection(enabled)))
