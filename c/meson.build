if get_option('build_c').enabled()
  c_header = custom_target('c_header', command: generator_command, input: files('vkfl.h.in'), output: '@BASENAME@',
                           build_by_default: true)
  c_source = custom_target('c_source', command: generator_command, input: files('vkfl.c.in'), output: '@BASENAME@',
                           build_by_default: true)
  vkfl_c_dep = declare_dependency(sources: [ c_header, c_source ])
  doc_deps += [ c_header, c_source ]
endif
