#!/usr/bin/env python3
#
# Copyright 2021 Alexander Rothman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime
from pathlib import Path

from mako.template import Template

from generatorlib.vulkan import parse_vulkan_spec, VulkanVersion, VulkanCommandType

def comma_separated(s: str):
    res = set()
    for value in s.split(','):
        if len(value) > 0:
            res.add(value.replace('\"', '').replace('\'', ''))
    return res

def has_extension(e: str, l: list[str]) -> bool:
    return True if ("all" in l) or (e in l) else False

def main():
    epilog = """
    If a specification path is not explicitly provided, the following locations are searched.
    Unix-like systems:
    \t$VULKAN_SDK/share/vulkan/registry/vk.xml
    \t$HOME/.local/share/vulkan/registry/vk.xml
    \t/usr/local/share/vulkan/registry/vk.xml
    \t/usr/share/vulkan/registry/vk.xml
    Windows systems:
    \t%VULKAN_SDK%/share/vulkan/registry/vk.xml
    \t%VULKAN_SDK_PATH%/share/vulkan/registry/vk.xml
    """.expandtabs(2)
    parser = ArgumentParser(epilog=epilog, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("--spec", type=Path, help="A file path to an XML specification of the " +
                        "Vulkan API. If this isn't provided, the script will default to searching a set of standard " +
                        "paths for vk.xml.", default=None)
    parser.add_argument("--extensions", type=comma_separated, default=["all"],
                        help="A comma separated list of Vulkan extensions to include in the loader. " +
                             "This may also be the special value \"all\". Defaults to \"all\".")
    parser.add_argument("--api", default="vulkan",
                        help="The Vulkan API to include in the loader (e.g., \"vulkan\", \"vulkansc\"). Defaults to " +
                             "\"vulkan\".")
    parser.add_argument("--api-version", default="latest",
                        help="The latest Vulkan API version to include in the loader (e.g., 1.0, 1.1, 1.2, etc.). " +
                             "This may also be the special value \"latest\". Defaults to \"latest\".")
    parser.add_argument("--no-enable-deprecated-features", const=False, action="store_const", default=True,
                        help="Disable the generation of deprecated features (i.e., extensions). Deprecated features " +
                             "are marked as disabled.")
    parser.add_argument("--no-generate-disabled-defines", const=False, action="store_const", default=True,
                        help="Disable the generation of symbols indicating that an extension or API version is " +
                             "disabled (i.e., don't generate VKFL_X_ENABLED if it would be defined as 0).")
    parser.add_argument("INPUT", type=Path, help="A path to an input template file.")
    parser.add_argument("OUTPUT", type=Path, help="A path to an output file.")
    args = parser.parse_args()
    (apis, extensions, commands, spec_version) = parse_vulkan_spec(args.spec)
    enabled_extensions = { }
    disabled_extensions = { }
    for extension in extensions:
        possible = extensions[extension]
        has_ext = has_extension(extension, args.extensions)
        supported = args.api in possible.supported_apis() and (not possible.deprecated())
        if has_ext and supported:
            enabled_extensions[extension] = possible
    else:
        disabled_extensions[extension] = possible
    enabled_apis = { }
    disabled_apis = { }
    if args.api_version == "latest":
        for api in apis:
            if args.api in apis[api].supported_apis():
                enabled_apis[api] = apis[api]
            else:
                disabled_apis[api] = apis[api]
    else:
        desired = VulkanVersion(args.api_version)
        for api in apis:
            if (apis[api].version() <= desired) and (args.api in apis[api].supported_apis()):
                enabled_apis[api] = apis[api]
            else:
                disabled_apis[api] = apis[api]
    enabled_global_commands = set()
    enabled_instance_commands = set()
    enabled_device_commands = set()
    for api in enabled_apis:
        for command in enabled_apis[api].commands():
            command_type = commands[command].type()
            if command_type == VulkanCommandType.GLOBAL:
                enabled_global_commands.add(command)
            elif command_type == VulkanCommandType.INSTANCE:
                enabled_instance_commands.add(command)
            elif command_type == VulkanCommandType.DEVICE:
                enabled_device_commands.add(command)
        for command in enabled_apis[api].removals():
            command_type = commands[command].type()
            if (command_type == VulkanCommandType.GLOBAL):
                enabled_global_commands.discard(command)
            elif (command_type == VulkanCommandType.INSTANCE):
                enabled_instance_commands.discard(command)
            elif command_type == VulkanCommandType.DEVICE:
                enabled_device_commands.discard(command)
    for extension in enabled_extensions:
        for command in enabled_extensions[extension].commands():
            command_type = commands[command].type()
            if command_type == VulkanCommandType.GLOBAL:
                enabled_global_commands.add(command)
            elif command_type == VulkanCommandType.INSTANCE:
                enabled_instance_commands.add(command)
            elif command_type == VulkanCommandType.DEVICE:
                enabled_device_commands.add(command)
    template = Template(filename=args.INPUT.absolute().as_posix(), output_encoding="utf-8")
    source = template.render(enabled_apis=enabled_apis, disabled_apis=disabled_apis,
                             enabled_extensions=enabled_extensions, disabled_extensions=disabled_extensions,
                             enabled_global_commands=enabled_global_commands,
                             enabled_instance_commands=enabled_instance_commands,
                             enabled_device_commands=enabled_device_commands, spec_version=spec_version,
                             generate_disabled_defines=args.no_generate_disabled_defines,
                             buildtime=datetime.utcnow())
    with open(args.OUTPUT, "wb") as file:
        file.write(source)

if __name__ == "__main__":
    main()
