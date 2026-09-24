import inspect
from importlib.metadata import PackageNotFoundError, version

import deepagents
from deepagents import create_deep_agent
from deepagents.middleware import SubAgent


def get_package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Package version not found"


# print("=" * 80)
# print("DEEPAGENTS INFORMATION")
# print("=" * 80)

# print(f"Module location: {deepagents.__file__}")
# print(f"Installed version: {get_package_version('deepagents')}")


# print("\n" + "=" * 80)
# print("create_deep_agent")
# print("=" * 80)

try:
    print(inspect.signature(create_deep_agent))
except (TypeError, ValueError) as exc:
    print(f"Could not inspect signature: {exc}")


# print("\n" + "=" * 80)
# print("SubAgent")
# print("=" * 80)

# print(f"Object: {SubAgent}")
# print(f"Type: {type(SubAgent)}")
# print(f"Module: {getattr(SubAgent, '__module__', 'Unknown')}")
# print(f"Base classes: {getattr(SubAgent, '__mro__', 'Unavailable')}")


# print("\nSubAgent fields:")

annotations = getattr(SubAgent, "__annotations__", {})

if annotations:
    for field_name, field_type in annotations.items():
        print(f"  {field_name}: {field_type}")
else:
    print("  No field annotations were found.")


required_keys = getattr(SubAgent, "__required_keys__", set())
optional_keys = getattr(SubAgent, "__optional_keys__", set())

print("\nRequired keys:")

if required_keys:
    for key in sorted(required_keys):
        print(f"  - {key}")
else:
    print("  None reported")


print("\nOptional keys:")

if optional_keys:
    for key in sorted(optional_keys):
        print(f"  - {key}")
else:
    print("  None reported")


print("\n" + "=" * 80)
print("SUBAGENT CONSTRUCTION TEST")
print("=" * 80)

try:
    test_subagent = SubAgent(
        name="test_agent",
        description="Temporary compatibility test agent.",
        system_prompt="You are a test agent.",
    )

    print("SubAgent construction succeeded.")
    print(f"Created object type: {type(test_subagent)}")
    print(f"Created object: {test_subagent}")

except Exception as exc:
    print("SubAgent construction failed.")
    print(f"Error type: {type(exc).__name__}")
    print(f"Error: {exc}")
