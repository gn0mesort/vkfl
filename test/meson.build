if get_option('build_tests').enabled()
  if get_option('build_cpp').enabled()
    test_cpp_global_exe = executable('cpp-global-function-load', files('test_global.cpp'),
                                     dependencies: [ vkfl_cpp_dep, vulkan_dep ])
    test('cpp-global-function-load', test_cpp_global_exe)
    test_cpp_instance_exe = executable('cpp-instance-function-load', files('test_instance.cpp'),
                                       dependencies: [ vkfl_cpp_dep, vulkan_dep ])
    test('cpp-instance-function-load', test_cpp_instance_exe)
    test_cpp_device_exe = executable('cpp-device-function-load', files('test_device.cpp'),
                                     dependencies: [ vkfl_cpp_dep, vulkan_dep ])
    test('cpp-device-function-load', test_cpp_device_exe)
  endif
  if get_option('build_c').enabled()
    test_c_global_exe = executable('c-global-function-load', files('test_global.c'),
                                   dependencies: [ vkfl_c_dep, vulkan_dep ])
    test('c-global-function-load', test_c_global_exe)
    test_c_instance_exe = executable('c-instance-function-load', files('test_instance.c'),
                                     dependencies: [ vkfl_c_dep, vulkan_dep ])
    test('c-instance-function-load', test_c_instance_exe)
    test_c_device_exe = executable('c-device-function-load', files('test_device.c'),
                                   dependencies: [ vkfl_c_dep, vulkan_dep ])
    test('c-device-function-load', test_c_device_exe)
    test_c_allocation_exe = executable('c-allocation', files('test_allocation.c'),
                                       dependencies: [ vkfl_c_dep, vulkan_dep ])
    test('c-allocation', test_c_allocation_exe)
  endif
endif
