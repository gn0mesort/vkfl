/**
 * Copyright 2022 Alexander Rothman
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include <inttypes.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include <vulkan/vulkan.h>

#include "vkfl.h"

void error(const char *const message) {
  fprintf(stderr, "Error: %s\n", message);
  exit(1);
}

int main() {
  // Create a loader and load global function pointers.
  struct vkfl_loader* ld = vkfl_create_loader(vkGetInstanceProcAddr, NULL);
  if (!ld)
  {
    error("Failed to create vkfl_loader.");
  }
  VkApplicationInfo app_info;
  memset(&app_info, 0, sizeof(VkApplicationInfo));
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app_info.apiVersion = VK_VERSION_1_2;
  VkInstanceCreateInfo instance_info;
  memset(&instance_info, 0, sizeof(VkInstanceCreateInfo));
  instance_info.sType = VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO;
  instance_info.pApplicationInfo = &app_info;
  // Resolve a function pointer.
  // Note that to do anything useful with the resulting function pointer it needs to be cast to the correct type.
  // vkfl.h does not introduce these types so you need vulkan.h as well.
  PFN_vkCreateInstance create_instance = (PFN_vkCreateInstance) vkfl_get(ld, VKFL_COMMAND_vkCreateInstance);
  if (!create_instance)
  {
    error("Failed to load \"vkCreateInstance\".");
  }
  VkInstance instance;
  VkResult res = create_instance(&instance_info, NULL, &instance);
  if (res != VK_SUCCESS)
  {
    error("Failed to create Vulkan instance.");
  }
  // Update the loader with instance function pointers.
  if (vkfl_load_instance(ld, instance) < 0)
  {
    error("Failed to load Vulkan instance functions.");
  }
  PFN_vkEnumeratePhysicalDevices enumerate_physical_devices =
    (PFN_vkEnumeratePhysicalDevices) vkfl_get(ld, VKFL_COMMAND_vkEnumeratePhysicalDevices);
  if (!enumerate_physical_devices)
  {
    error("Failed to load \"vkEnumeratePhysicalDevices\".");
  }
  uint32_t sz = 1;
  VkPhysicalDevice pdev;
  res = enumerate_physical_devices(instance, &sz, &pdev);
  if (res < VK_SUCCESS)
  {
    error("Failed to enumerate Vulkan physical devices.");
  }
  VkDeviceCreateInfo device_info;
  memset(&device_info, 0, sizeof(VkDeviceCreateInfo));
  device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  PFN_vkCreateDevice create_device = (PFN_vkCreateDevice) vkfl_get(ld, VKFL_COMMAND_vkCreateDevice);
  if (!create_device)
  {
    error("Failed to load \"vkCreateDevice\".");
  }
  VkDevice device;
  res = create_device(pdev, &device_info, NULL, &device);
  if (res != VK_SUCCESS)
  {
    error("Failed to create Vulkan device.");
  }
  // Update the loader with device function pointers.
  if (vkfl_load_device(ld, device) < 0)
  {
    error("Failed to load Vulkan device functions.");
  }
  printf("Successfully created Vulkan environment!\n");
  PFN_vkDestroyDevice destroy_device = (PFN_vkDestroyDevice) vkfl_get(ld, VKFL_COMMAND_vkDestroyDevice);
  if (!destroy_device)
  {
    error("Failed to load \"vkDestroyDevice\".");
  }
  destroy_device(device, NULL);
  // After destroying the loaded device you may wish to clear the corresponding function pointers.
  // This will reload the instance function pointers in place of device pointers.
  (void) vkfl_unload_device(ld);
  PFN_vkDestroyInstance destroy_instance = (PFN_vkDestroyInstance) vkfl_get(ld, VKFL_COMMAND_vkDestroyInstance);
  if (!destroy_instance)
  {
    error("Failed to load \"vkDestroyInstance\".");
  }
  destroy_instance(instance, NULL);
  // As with the device, instance function pointers can be cleared.
  // This reverts the entire loader to the state it was in just after construction.
  (void) vkfl_unload_instance(ld);
  vkfl_destroy_loader(ld, NULL);
  printf("Successfully destroyed Vulkan environment!\n");
  return 0;
}
