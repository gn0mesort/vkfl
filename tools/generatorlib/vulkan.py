import os
import sys
from enum import Enum
from pathlib import Path

from defusedxml import ElementTree

class VulkanVersion:
    def __init__(self, version: str):
        parts = version.strip().split('.')
        assert len(parts) >= 1
        self._major = int(parts[0])
        if len(parts) == 1:
            self._minor = 0
        else:
            self._minor = int(parts[1])

    def major(self) -> int:
        return self._major

    def minor(self) -> int:
        return self._minor

    def compare(self, other) -> int:
        res = self._major - other._major
        if res == 0:
            res = self._minor - other._minor
        return res

    def __eq__(self, other) -> bool:
        return self.compare(other) == 0

    def __lt__(self, other) -> bool:
        return self.compare(other) < 0

    def __le__(self, other) -> bool:
        return self.compare(other) <= 0

    def __str__(self) -> str:
        return f"{self._major}.{self._minor}"

class VulkanCommandType(Enum):
    GLOBAL = 0,
    INSTANCE = 1,
    DEVICE = 2

class VulkanCommand:
    def __init__(self, tree, node):
        self._original_node = node
        aliased_command = node.get("alias")
        if aliased_command:
            self._name = node.get("name")
            node = tree.find(f"commands/command/proto/name[.='{aliased_command}']/../..")
        else:
            self._name = node.findtext("proto/name")
        assert self._name.startswith("vk")
        global_fns = ("vkEnumerateInstanceVersion", "vkEnumerateInstanceExtensionProperties",
                      "vkEnumerateInstanceLayerProperties", "vkCreateInstance", "vkGetInstanceProcAddr")
        if self._name in global_fns:
            self._type = VulkanCommandType.GLOBAL
        else:
            owner = node.findtext("param[1]/type")
            if owner in ("VkInstance", "VkPhysicalDevice"):
                self._type = VulkanCommandType.INSTANCE
            elif owner in ("VkDevice", "VkCommandBuffer", "VkQueue"):
                self._type = VulkanCommandType.DEVICE
            else:
                assert False
        self._node = node

    def name(self) -> str:
        return self._name

    def type(self) -> VulkanCommandType:
        return self._type

    def node(self):
        return self._node

class VulkanFeature:
    def __init__(self, node):
        self._node = node
        if node.tag == "feature":
            self._version = VulkanVersion(node.get("number"))
            self._name = node.get("name")
            self._supported_apis = set()
            for api in node.get("api").split(","):
                self._supported_apis.add(api)
        else:
            self._name = node.get("name")
            self._supported_apis = set()
            for api in node.get("supported").split(","):
                self._supported_apis.add(api)
            version_node = node.find(f"require/enum[@name='{self._name.upper()}_SPEC_VERSION']")
            # This is inexplicable to me. Originally, I tried if version_node but that doesn't seem to work.
            if version_node is not None and version_node.get("value") is not None:
                self._version = VulkanVersion(version_node.get("value"))
            else:
                self._version = VulkanVersion("0.0")
        self._enabled = False
        self._commands = set()
        for command in node.findall("require/command"):
            self._commands.add(command.get("name"))
        self._removals = set()
        for command in node.findall("remove/command"):
            self._removals.add(command.get("name"))

    def node(self):
        return self._node

    def name(self) -> str:
        return self._name

    def supported_apis(self) -> set[str]:
        return self._supported_apis

    def version(self) -> VulkanVersion:
        return self._version

    def enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def commands(self) -> set[str]:
        return self._commands

    def removals(self) -> set[str]:
        return self._removals

def _find_spec(search_paths: list[Path]) -> Path:
    for search_path in search_paths:
        complete_path = search_path.joinpath("share/vulkan/registry/vk.xml").absolute()
        if complete_path.exists() and complete_path.is_file():
            return complete_path
    return None

def _parse_commands(spec_tree):
    res = { }
    for command in spec_tree.findall("commands/command"):
        parsed = VulkanCommand(spec_tree, command)
        res[parsed.name()] = parsed
    return res

def _parse_apis(spec_tree):
    res = { }
    for feature in spec_tree.findall("feature"):
        parsed = VulkanFeature(feature)
        res[parsed.name()] = parsed
    return res

def _parse_extensions(spec_tree):
    res = { }
    for feature in spec_tree.findall("extensions/extension"):
        parsed = VulkanFeature(feature)
        res[parsed.name()] = parsed
    return res


def parse_vulkan_spec(spec_path: Path):
    if spec_path is None:
        if ((sys.platform == "win32" or sys.platform == "cygwin") and
            ("VULKAN_SDK" in os.environ or "VULKAN_SDK_PATH" in os.environ)):
            spec_path = _find_spec([ Path(os.environ["VULKAN_SDK"]), Path(os.environ["VULKAN_SDK_PATH"]) ])
        else:
            search_paths = [ ]
            if "VULKAN_SDK" in os.environ:
                search_paths.append(Path(os.environ["VULKAN_SDK"]))
            search_paths.extend([ Path.home().joinpath(".local"), Path("/usr/local"), Path("/usr") ])
            spec_path = _find_spec(search_paths)
    spec_tree = None
    with open(spec_path, "r") as spec_file:
        spec_tree = ElementTree.parse(spec_file)
    commands = _parse_commands(spec_tree)
    apis = _parse_apis(spec_tree)
    extensions = _parse_extensions(spec_tree)
    spec_version = spec_tree.find("types/type[name='VK_HEADER_VERSION']").find("name").tail.strip()
    return (apis, extensions, commands, spec_version)

