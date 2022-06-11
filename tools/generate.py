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
# Portions of this file are from volk (https://github.com/zeux/volk/)
# volk is provided under the following license:
#
# Copyright (c) 2018-2019 Arseny Kapoulkine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
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
"""
parser = ArgumentParser(epilog=epilog, formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("--spec", type=Path, help="A file path to an XML specification of the " +
                    "Vulkan API. If this isn't provided, the script will default to searching a set of standard " +
                    "paths for vk.xml.", default=None)
parser.add_argument("--extensions", type=comma_separated, default=["all"],
                    help="A comma separated list of Vulkan extensions to include in the loader. " +
                         "This may also be the special value \"all\". Defaults to \"all\".")
parser.add_argument("--api", default="latest",
                    help="The latest Vulkan API version to include in the loader (i.e. 1.0, 1.1, 1.2, etc.). " +
                         "This may also be the special value \"latest\". Defaults to \"latest\".")
parser.add_argument("--no-generate-disabled-defines", const=False, action="store_const", default=True,
                    help="Disable the generation of symbols indicating that an extension or API version is disabled" +
                         " (i.e., don't generate VKFL_X_ENABLED if it would be defined as 0).")
parser.add_argument("INPUT", type=Path, help="A path to an input template file.")
parser.add_argument("OUTPUT", type=Path, help="A path to an output file.")
args = parser.parse_args()
(apis, extensions, commands, spec_version) = parse_vulkan_spec(args.spec)
enabled_extensions = None
disabled_extensions = { }
if "all" in args.extensions:
    enabled_extensions = extensions
else:
    enabled_extensions = { }
    for extension in extensions:
        if extension in args.extensions:
            enabled_extensions[extension] = extensions[extension]
        else:
            disabled_extensions[extension] = extensions[extension]
enabled_apis = None
disabled_apis = { }
if args.api == "latest":
    enabled_apis = apis
else:
    enabled_apis = { }
    desired = VulkanVersion(args.api)
    for api in apis:
        if apis[api].version() <= desired:
            enabled_apis[api] = apis[api]
        else:
            disabled_apis[api] = apis[api]
enabled_global_commands = [ ]
enabled_instance_commands = [ ]
enabled_device_commands = [ ]
for api in enabled_apis:
    for command in enabled_apis[api].commands():
        command_type = commands[command].type()
        if command_type == VulkanCommandType.GLOBAL:
            enabled_global_commands.append(command)
        elif command_type == VulkanCommandType.INSTANCE:
            enabled_instance_commands.append(command)
        elif command_type == VulkanCommandType.DEVICE:
            enabled_device_commands.append(command)
for extension in enabled_extensions:
    for command in enabled_extensions[extension].commands():
        command_type = commands[command].type()
        if command_type == VulkanCommandType.GLOBAL:
            enabled_global_commands.append(command)
        elif command_type == VulkanCommandType.INSTANCE:
            enabled_instance_commands.append(command)
        elif command_type == VulkanCommandType.DEVICE:
            enabled_device_commands.append(command)
template = Template(filename=args.INPUT.as_posix(), output_encoding="utf-8")
source = template.render(enabled_apis=enabled_apis, disabled_apis=disabled_apis,
                         enabled_extensions=enabled_extensions, disabled_extensions=disabled_extensions,
                         enabled_global_commands=enabled_global_commands,
                         enabled_instance_commands=enabled_instance_commands,
                         enabled_device_commands=enabled_device_commands, spec_version=spec_version,
                         generate_disabled_defines=args.no_generate_disabled_defines,
                         buildtime=datetime.utcnow())
with open(args.OUTPUT, "wb") as file:
    file.write(source)
