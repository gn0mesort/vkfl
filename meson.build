project(
  'vkfl',
  [ 'c', 'cpp' ],
  version: '1.3.0',
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

if not (get_option('build_cpp').enabled() and get_option('build_c').enabled())
  warning('Both C and C++ targets are disabled.')
endif

generator_args = [ ]
if get_option('specification') != 'default'
  spec_file = files(get_option('specification'))[0]
  generator_args += '--spec=@0@'.format(spec_file)
endif
if get_option('api') != 'latest'
  generator_args += '--api=@0@'.format(get_option('api'))
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
if get_option('generate_extra_defines')
  generator_args += '--generate-extra-defines'
endif
# Check for Python3
find_program('python3')
generator_command = [ find_program('tools/generate.py'), generator_args, '@INPUT@', '@OUTPUT@' ]
doc_deps = [ ]
vkfl_c_dep = disabler()
vkfl_cpp_dep = disabler()
subdir('include')
subdir('src')

doxygen = find_program('doxygen', required: false, disabler: true)
vkfl_docs = run_target('documentation', command: [ doxygen, files('Doxyfile') ], depends: doc_deps)
vulkan_dep = dependency('vulkan',
                        required: get_option('build_tests').enabled() or get_option('build_examples').enabled(),
                        disabler: true, version: '>=1.0.0')
subdir('test')
subdir('examples')
