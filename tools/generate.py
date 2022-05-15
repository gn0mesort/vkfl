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
import os
import sys
from xml.etree import ElementTree
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime
from pathlib import Path

def parse_xml(path: Path):
    with open(path, 'r') as file:
        return ElementTree.parse(file)

def is_descendent(vk_types, name, base):
    if name == base:
        return True
    current = vk_types.get(name)
    if not current:
        return False
    parents = current.get('parent')
    if not parents:
        return False
    return any([ is_descendent(vk_types, parent, base) for parent in parents.split(',') ])

LD_GLOBAL = 0
LD_INSTANCE = 1
LD_DEVICE = 2

def identify_group(vk_types, command):
    vk_global_pfns = set([ 'vkEnumerateInstanceVersion', 'vkEnumerateInstanceExtensionProperties',
                           'vkEnumerateInstanceLayerProperties', 'vkCreateInstance', 'vkGetInstanceProcAddr' ])
    name = command.findtext('proto/name')
    owner = command.findtext('param[1]/type')
    if name in vk_global_pfns:
        return LD_GLOBAL
    if name != 'vkGetDeviceProcAddr' and is_descendent(vk_types, owner, 'VkDevice'):
        return LD_DEVICE
    return LD_INSTANCE

def commands_str(commands):
    result = ''
    for command in commands:
        name = command['name']
        result += f'\t\t{name[2:]},{os.linesep}'
    return result.strip().expandtabs(2)

def c_commands_str(commands):
    result = ''
    for command in commands:
        name = command['name']
        result += f'\t\tVKFL_COMMAND_{name[2:]},{os.linesep}'
    return result.strip().expandtabs(2)

def command_count_str(commands):
    return str(len(commands))

def defines_str(apis, exts, generate_extra_defines: bool):
    result = ''
    for api in apis:
        symbol = api.replace('VK_VERSION', 'VKFL_API').upper() + '_ENABLED'
        result += f"#define {symbol} {1 if apis[api]['enabled'] else 0}{os.linesep}"
    for ext in exts:
        symbol = ext.replace('VK', 'VKFL', 1).upper()
        result += f"#define {symbol}_ENABLED {1 if exts[ext]['enabled'] else 0}{os.linesep}"
        if exts[ext]['enabled'] and generate_extra_defines:
            sym_name = f'{symbol}_EXTENSION_NAME'
            result += f'#define {sym_name} \"{ext}\"{os.linesep}'
            sym_version = f'{symbol}_SPEC_VERSION'
            result += f"#define {sym_version} {exts[ext]['version']}{os.linesep}"
    time = datetime.utcnow()
    result += f'#define VKFL_BUILD_DATE {time.year}{time.month:02}{time.day:02}ULL{os.linesep}'
    result += f'#define VKFL_BUILD_TIME {time.hour}{time.minute:02}{time.second:02}ULL{os.linesep}'
    return result.rstrip().expandtabs(2)

def common_private_defines(global_commands, instance_commands, device_commands):
    result = ''
    result += f'#define VKFL_GLOBAL_MAX {len(global_commands)}{os.linesep}'
    result += f'#define VKFL_INSTANCE_MAX (VKFL_GLOBAL_MAX + {len(instance_commands)}){os.linesep}'
    result += f'#define VKFL_DEVICE_MAX (VKFL_INSTANCE_MAX + {len(device_commands)}){os.linesep}'
    result += f'#define VKFL_STRING(s) (#s){os.linesep}'
    return result

def private_defines_str(global_commands, instance_commands, device_commands):
    result = common_private_defines(global_commands, instance_commands, device_commands)
    result += f'#define V(cmd) (m_pfns[static_cast<std::size_t>(command::cmd)] = '
    result += f'context_loader(context, VKFL_STRING(vk##cmd))){os.linesep}'
    return result.rstrip().expandtabs(2)

def c_private_defines_str(global_commands, instance_commands, device_commands):
    result = common_private_defines(global_commands, instance_commands, device_commands)
    result += f'#define V(cmd) (dl->pfns[VKFL_COMMAND_##cmd] = context_loader(context, VKFL_STRING(vk##cmd)))'
    return result.rstrip().expandtabs(2)

def loader_str(commands, is_macro: bool):
    result = ''
    lineend = '\\' if is_macro else ''
    for command in commands:
        name = command['name']
        if name == 'vkGetInstanceProcAddr':
            continue
        result += f'\t\tV({name[2:]});{lineend}{os.linesep}'
    return result.rstrip().expandtabs(2)

def header_version_str(tree):
    return tree.find('types/type[name="VK_HEADER_VERSION"]').find('name').tail.strip()

def enabled_by_any(check_features: set[str], features: dict):
    res = False
    for key in check_features:
        res = res or features[key]['enabled']
    return res

def version_cmp(ver1: list[str], ver2: list[str]):
    major = int(ver1[0]) - int(ver2[0])
    if major == 0:
        return int(ver1[1]) - int(ver2[1])
    return major

def comma_separated(s: str):
    res = set()
    for value in s.split(','):
        if len(value) > 0:
            res.add(value.replace('\"', '').replace('\'', ''))
    return res

def spec_path(search_paths: list[Path]):
    for search_path in search_paths:
        if not search_path:
            continue
        registry = search_path.absolute().joinpath('share/vulkan/registry/vk.xml')
        if registry.exists() and registry.is_file():
            return registry
    return Path.cwd().joinpath('vk.xml').absolute()

default_spec = ''
if sys.platform == 'win32' or sys.platform == 'cygwin':
    default_spec = spec_path([ os.environ['VULKAN_SDK'], os.environ['VULKAN_SDK_PATH'] ])
# It's not clear to me that this is adequate with regard to Apple environments. Documentation for the LunarG
# Vulkan SDK indicates that the registry should be located at $VULKAN_SDK/share/registry/vk.xml as it is on Linux.
# Hopefully, using the same search as a Linux system is adequate.
else:
    default_spec = spec_path([ Path(os.environ['VULKAN_SDK']), Path.home().joinpath('.local'), Path('/usr/local'),
                               Path('/usr') ])
epilog = """
If a specification path is not explicitly provided, the following locations are searched.
Unix-like systems:
\t$VULKAN_SDK/share/vulkan/registry/vk.xml
\t$HOME/.local/share/vulkan/registry/vk.xml
\t/usr/local/share/vulkan/registry/vk.xml
\t/usr/share/vulkan/registry/vk.xml
\t$PWD/vk.xml
Windows systems:
\t%VULKAN_SDK%/share/vulkan/registry/vk.xml
\t%VULKAN_SDK_PATH%/share/vulkan/registry/vk.xml
\t%CD%/vk.xml
"""
parser = ArgumentParser(epilog=epilog, formatter_class=RawDescriptionHelpFormatter)

parser.add_argument('--spec', default=default_spec, type=Path, help='A file path to an XML specification of the ' +
                    'Vulkan API. If this isn\'t provided, the script will default to searching a set of standard ' +
                    'paths for vk.xml.')
parser.add_argument('--extensions', type=comma_separated, default='all',
                    help='A comma separated list of Vulkan extensions to include in the loader. ' +
                         'This may also be the special value \"all\". Defaults to \"all\".')
parser.add_argument('--api', default='latest',
                    help='The latest Vulkan API version to include in the loader (i.e. 1.0, 1.1, 1.2, etc.). ' +
                         'This may also be the special value \"latest\". Defaults to \"latest\".')
parser.add_argument('--generate-extra-defines', const=True, action='store_const', default=False,
                    help='Enable the generation of \"VKFL_X_EXTENSION_NAME\" and \"VKFL_X_SPEC_VERSION\" symbols. ' +
                         'This is disabled by default.')
parser.add_argument('INPUT', type=Path, help='A path to an input template file.')
parser.add_argument('OUTPUT', type=Path, help='A path to an output file.')
args = parser.parse_args()
tree = parse_xml(args.spec)
input_exts = args.extensions
use_all_exts = False
if 'all' in input_exts:
    use_all_exts = True
exts = { }
api_version = None
use_latest_api = False
if args.api == 'latest':
    use_latest_api = True
else:
    api_version = args.api.split('.')
generate_extra_defines = args.generate_extra_defines
apis = { }
vk_types = { }
for vk_type in tree.findall('types/type'):
    name = vk_type.findtext('name')
    vk_types[name] = vk_type
vk_commands = { }
for vk_command in tree.findall('commands/command'):
    alias = vk_command.get('alias')
    name = vk_command.get('name') if alias else vk_command.findtext('proto/name')
    vk_commands[name] = { }
    vk_commands[name]['name'] = name
    vk_commands[name]['element'] = vk_command
    vk_commands[name]['used_by_apis'] = set()
    vk_commands[name]['used_by_exts'] = set()
    ident_node = None
    if alias:
        vk_commands[name]['is_alias'] = True
        ident_node = tree.find(f'commands/command/proto/name[.="{alias}"]/../..')
    else:
        vk_commands[name]['is_alias'] = False
        ident_node = vk_command
    vk_commands[name]['loaded_from'] = identify_group(vk_types, ident_node)
for vk_feature in tree.findall('feature'):
    name = vk_feature.get('name')
    version = vk_feature.get('number').split('.')
    apis[name] = { 'enabled': False }
    if use_latest_api or version_cmp(version, api_version) <= 0:
        apis[name]['enabled'] = True
    for command in vk_feature.findall('require/command'):
        command_name = command.get('name')
        vk_commands[command_name]['used_by_apis'].add(name)
for vk_extension in tree.findall('extensions/extension'):
    name = vk_extension.get('name')
    exts[name] = { 'enabled': False, 'version': 0 }
    if use_all_exts or name in input_exts:
        exts[name]['enabled'] = True
    for requirement in vk_extension.findall('require'):
        for enum in requirement.findall('enum'):
            if enum.get('name') == f'{name.upper()}_SPEC_VERSION':
                value = enum.get('value')
                exts[name]['version'] = int(value) if value else 0
        for command in requirement.findall('command'):
            command_name = command.get('name')
            vk_commands[command_name]['used_by_exts'].add(name)
vk_global_commands = [ ]
vk_instance_commands = [ ]
vk_device_commands = [ ]
for vk_command in vk_commands:
    command = vk_commands[vk_command]
    if enabled_by_any(command['used_by_apis'], apis) or enabled_by_any(command['used_by_exts'], exts):
        if command['loaded_from'] == LD_GLOBAL:
            vk_global_commands.append(command)
        elif command['loaded_from'] == LD_INSTANCE:
            vk_instance_commands.append(command)
        elif command['loaded_from'] == LD_DEVICE:
            vk_device_commands.append(command)
key_fn = lambda command: command['name']
vk_all_commands = sorted(vk_global_commands, key=key_fn) + sorted(vk_instance_commands, key=key_fn)
vk_all_commands += sorted(vk_device_commands, key=key_fn)
text = ''
with open(args.INPUT, 'rb') as file:
    text = str(file.read(), 'utf-8')
text = text.replace('@commands@', commands_str(vk_all_commands))
text = text.replace('@commands_count@', command_count_str(vk_all_commands))
text = text.replace('@header_version@', header_version_str(tree))
text = text.replace('@load_global@', loader_str(vk_global_commands, False))
text = text.replace('@load_instance@', loader_str(vk_instance_commands, False))
text = text.replace('@load_device@', loader_str(vk_device_commands, False))
text = text.replace('@load_device_macro@', loader_str(vk_device_commands, True))
text = text.replace('@defines@', defines_str(apis, exts, generate_extra_defines))
text = text.replace('@private_defines@',
                    private_defines_str(vk_global_commands, vk_instance_commands, vk_device_commands))
text = text.replace('@c_commands@', c_commands_str(vk_all_commands))
text = text.replace('@c_private_defines@', c_private_defines_str(vk_global_commands, vk_instance_commands,
                                                                 vk_device_commands))
with open(args.OUTPUT, 'wb') as file:
    file.truncate()
    file.write(bytes(text, 'utf-8'))
