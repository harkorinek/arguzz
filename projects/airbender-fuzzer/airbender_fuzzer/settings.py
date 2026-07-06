from airbender_fuzzer.kinds import InjectionKind, InstrKind

#
# ZKVM Specific Versions and URLs
#

AIRBENDER_AVAILABLE_COMMITS_OR_BRANCHES = [
    "main",
]
AIRBENDER_ZKVM_GIT_REPOSITORY = "https://github.com/matter-labs/zksync-airbender"


# sets the appropriate rust toolchain version
def get_rust_toolchain_version(commit_or_branch: str) -> str:
    # sets the appropriate rust toolchain and target versions
    return "nightly-2025-07-25"


#
# Rust Magic Values
#

RUST_GUEST_RETURN_TYPE = "u32"
RUST_GUEST_CORRECT_VALUE = 0xDEADBEEF

#
# Flag to decide if division and modulo of 0 should be transformed
#

APPLY_SAFE_REM_DIV_TRANSFORMATION = True

#
# Special Timeout handling
#

TIMEOUT_PER_RUN = 60 * 4  # 4 min, in seconds
TIMEOUT_PER_BUILD = 60 * 30  # 30 min, in seconds

#
# Injection Specifics
#

ENABLED_INJECTION_KINDS: list[InjectionKind] = [
    # TODO: add kinds
]

# NOTE: empty list disables preferences
PREFERRED_INSTRUCTIONS: list[InstrKind] = []
