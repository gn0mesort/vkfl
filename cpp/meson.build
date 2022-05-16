if get_option('build_cpp').enabled()
  cpp_header = custom_target('cpp_header', command: generator_command, input: files('vkfl.hpp.in'),
                             output: '@BASENAME@', build_by_default: true)
  cpp_source = custom_target('cpp_source', command: generator_command, input: files('vkfl.cpp.in'),
                             output: '@BASENAME@', build_by_default: true)
  vkfl_cpp_dep = declare_dependency(sources: [ cpp_header, cpp_source ])
  doc_deps += [ cpp_header, cpp_source ]
endif
