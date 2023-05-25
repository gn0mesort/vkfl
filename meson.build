project(
  'vkfl',
  [ 'c', 'cpp' ],
  version: '2.0.0',
  meson_version: '>=0.62.2',
  license: 'Apache-2.0',
  default_options: [
    'c_std=c18',
    'c_link_args=-Wl,-rpath=$ORIGIN/../lib',
    'cpp_std=c++20',
    'cpp_link_args=-Wl,-rpath=$ORIGIN/../lib',
    'warning_level=3',
    'b_ndebug=if-release',
    'b_pie=true'
  ]
)

python = import('python')

if not (get_option('build_cpp').enabled() or get_option('build_c').enabled())
  warning('Both C and C++ targets are disabled.')
endif

generator_args = [ ]
if get_option('specification') != 'default'
  spec_file = files(get_option('specification'))[0]
  generator_args += '--spec=@0@'.format(spec_file)
endif
if get_option('api') != 'vulkan'
  generator_args += '--api=@0@'.format(get_option('api'))
endif
if get_option('api_version') != 'latest'
  generator_args += '--api-version=@0@'.format(get_option('api_version'))
endif
extension_arr = get_option('extensions')
if extension_arr.length() != 0
  if extension_arr[0] != 'all'
    extensions = '--extensions='
    foreach extension : get_option('extensions')
      extensions += '@0@,'.format(extension)
    endforeach
    generator_args += extensions
  endif
else
  generator_args += '--extensions=""'
endif
if not get_option('generate_disabled_defines')
  generator_args += '--no-generate-disbale-defines'
endif
# Ensure Python and required modules are fulfilled
py3 = python.find_installation('python3', modules: [ 'mako', 'defusedxml' ])
generator_command = [ find_program('tools/generate.py'), generator_args, '@INPUT@', '@OUTPUT@' ]
doc_deps = [ ]
vkfl_cpp_dep = disabler()
vkfl_cpp_files = [ ]
vkfl_c_dep = disabler()
vkfl_c_files = [ ]
subdir('include')
subdir('src')
if get_option('build_cpp').enabled()
  doc_deps += vkfl_cpp_files
  vkfl_cpp_dep = declare_dependency(sources: vkfl_cpp_files)
endif
if get_option('build_c').enabled()
  doc_deps += vkfl_c_files
  vkfl_c_dep = declare_dependency(sources: vkfl_c_files)
endif

doxygen = find_program('doxygen', required: false, disabler: true)
vkfl_docs = run_target('documentation', command: [ doxygen, files('Doxyfile') ], depends: doc_deps)
vulkan_dep = dependency('vulkan',
                        required: get_option('build_tests').enabled() or get_option('build_examples').enabled(),
                        disabler: true, version: '>=1.0.0')
subdir('test')
subdir('examples')
