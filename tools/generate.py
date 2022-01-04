#!/usr/bin/env python3
import os
from urllib.request import urlopen
from xml.etree import ElementTree as etree
from argparse import ArgumentParser
from datetime import datetime

def parse_xml(path):
    file = urlopen(path) if path.startswith('http') else open(path, 'r')
    with file:
        return etree.parse(file)

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

def command_count_str(commands):
    return str(len(commands))

def defines_str(apis, exts):
    result = ''
    for api in apis:
        symbol = api.replace('VK_VERSION', 'VKFL_USE_API')
        result += f'#define {symbol} 1{os.linesep}'
    for ext in exts:
        symbol = ext.replace('VK', 'VKFL_USE_EXTENSION', 1).upper()
        result += f'#define {symbol} 1{os.linesep}'
    time = datetime.utcnow()
    result += f'#define VKFL_BUILD_DATE {time.year}{time.month:02}{time.day:02}ULL{os.linesep}'
    result += f'#define VKFL_BUILD_TIME {time.hour}{time.minute:02}{time.second:02}ULL{os.linesep}'
    return result.rstrip()

def private_defines_str(global_commands, instance_commands, device_commands):
    result = ''
    result += f'#define VKFL_GLOBAL_MAX {len(global_commands)}{os.linesep}'
    result += f'#define VKFL_INSTANCE_MAX (VKFL_GLOBAL_MAX + {len(instance_commands)}){os.linesep}'
    result += f'#define VKFL_DEVICE_MAX (VKFL_INSTANCE_MAX + {len(device_commands)})'
    return result.rstrip()

def loader_str(commands):
    result = ''
    for command in commands:
        name = command['name']
        if name == 'vkGetInstanceProcAddr':
            continue
        result += f'\t\tm_pfns[static_cast<std::size_t>(command::{name[2:]})] = '
        result += f'context_loader(context, "{name}");{os.linesep}'
    return result.rstrip().expandtabs(2)

def header_version_str(tree):
    return tree.find('types/type[name="VK_HEADER_VERSION"]').find('name').tail.strip()

VK_SPEC = 'https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/xml/vk.xml'

parser = ArgumentParser()
parser.add_argument('--spec', type=str, default=VK_SPEC,
                    help='Specifies the URI to load the XML Vulkan specification from.')
parser.add_argument('--extensions', type=str, default='all',
                    help='A comma separated list of Vulkan extensions to include in the loader.' +
                         'This may also be the special value \"all\".')
parser.add_argument('--api', type=str, default='latest',
                    help='The latest Vulkan API version to include in the loader (i.e. 1.0, 1.1, 1.2, etc.).'
                         'This may also be the special value \"latest\".')
parser.add_argument('INPUT', type=str)
parser.add_argument('OUTPUT', type=str)
args = parser.parse_args()
tree = parse_xml(args.spec)
input_exts = set(args.extensions.split(','))
use_all_exts = False
if 'all' in input_exts:
    use_all_exts = True
exts = set()
api_version = None
use_latest_api = False
if args.api == 'latest':
    use_latest_api = True
else:
    api_version = float(args.api)
apis = set()
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
    version = float(vk_feature.get('number'))
    if use_latest_api or version - api_version < 0.00001:
        apis.add(name)
    for command in vk_feature.findall('require/command'):
        command_name = command.get('name')
        vk_commands[command_name]['used_by_apis'].add(name)
for vk_extension in tree.findall('extensions/extension'):
    name = vk_extension.get('name')
    for requirement in vk_extension.findall('require'):
        if use_all_exts or name in input_exts:
            exts.add(name)
        for command in requirement.findall('command'):
            command_name = command.get('name')
            vk_commands[command_name]['used_by_exts'].add(name)
vk_global_commands = [ ]
vk_instance_commands = [ ]
vk_device_commands = [ ]
for vk_command in vk_commands:
    command = vk_commands[vk_command]
    if not apis.isdisjoint(command['used_by_apis']) or not exts.isdisjoint(command['used_by_exts']):
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
text = text.replace('@load_global@', loader_str(vk_global_commands))
text = text.replace('@load_instance@', loader_str(vk_instance_commands))
text = text.replace('@load_device@', loader_str(vk_device_commands))
text = text.replace('@defines@', defines_str(apis, exts))
text = text.replace('@private_defines@',
                    private_defines_str(vk_global_commands, vk_instance_commands, vk_device_commands))
with open(args.OUTPUT, 'wb') as file:
    file.truncate()
    file.write(bytes(text, 'utf-8'))
