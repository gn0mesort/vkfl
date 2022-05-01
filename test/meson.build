if get_option('enable_tests')
  test_global_exe = executable('global-function-load', files('test_global.cpp'),
                               dependencies: [ vkfl_dep, vulkan_dep ])
  test('global-function-load', test_global_exe)
  test_instance_exe = executable('instance-function-load', files('test_instance.cpp'),
                                 dependencies: [ vkfl_dep, vulkan_dep ])
  test('instance-function-load', test_instance_exe)
  test_device_exe = executable('device-function-load', files('test_device.cpp'),
                               dependencies: [ vkfl_dep, vulkan_dep ])
  test('device-function-load', test_device_exe)
endif
