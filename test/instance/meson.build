if true
  test_srcs = [ 'test_instance.cpp' ]
  test_deps = [ vulkan_function_loader_dep, dependency('vulkan') ]
  test_exe = executable('instance-function-load', test_srcs, dependencies: test_deps)
  test('instance-function-load', test_exe)
endif
