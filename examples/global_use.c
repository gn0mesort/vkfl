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
/*
 * This demonstrates use of a vkfl::loader as a global object.
 */
#include <inttypes.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>


#include "vkfl.h"
// VK_NO_PROTOTYPES isn't required for regular usage of vkfl. However, in this case it's useful to demonstrate
// that the standard Vulkan function prototypes aren't necessary.
#define VK_NO_PROTOTYPES 1
#include <vulkan/vulkan_core.h>

// This is required for dlopen and dlsym. These functions are standard on POSIX systems.
// Using the equivalent functionality on Windows (LoadLibrary and GetProcAddress) doesn't affect usage beyond
// resolving vkGetInstanceProcAddr.
#include <dlfcn.h>

// Define a macro for retrieving and casting function pointers from the global loader.
#define VK_GET_PFN(cmd) \
  ((PFN_vk##cmd) vkfl_get(g_loader, VKFL_COMMAND_##cmd))

// Define command function macros. This could be done by a script to generate macros for all enabled functions.
#define vkGetInstanceProcAddr VK_GET_PFN(GetInstanceProcAddr)
#define vkEnumerateInstanceVersion VK_GET_PFN(EnumerateInstanceVersion)
#define vkCreateInstance VK_GET_PFN(CreateInstance)
#define vkDestroyInstance VK_GET_PFN(DestroyInstance)
#define vkEnumeratePhysicalDevices VK_GET_PFN(EnumeratePhysicalDevices)
#define vkGetPhysicalDeviceProperties VK_GET_PFN(GetPhysicalDeviceProperties)
#define vkCreateDevice VK_GET_PFN(CreateDevice)
#define vkDestroyDevice VK_GET_PFN(DestroyDevice)

// Due to using dlopen the vkfl::loader can't be initialized statically (as it requires a valid pointer to
// vkGetInstanceProcAddr during construction). An alternative to this would be to declare the prototype for
// vkGetInstanceProcAddr yourself prior to declaring the loader.
struct vkfl_loader* g_loader;

void error(const char *const message) {
  fprintf(stderr, "Error: %s\n", message);
  exit(1);
}
// Functions to load each level of Vulkan functionality.
void vulkan_create_loader(const PFN_vkGetInstanceProcAddr gipa) {
  g_loader = vkfl_create_loader(gipa, NULL);
  if (!g_loader)
  {
    error("Failed to create vkfl_loader.");
  }
}

void vulkan_load_instance(const VkInstance instance) {
  if (vkfl_load_instance(g_loader, instance) < 0)
  {
    error("Failed to load Vulkan instance functions.");
  }
}

void vulkan_load_device(const VkDevice device) {
  if (vkfl_load_device(g_loader, device) < 0)
  {
    error("Failed to load Vulkan device functions.");
  }
}

void vulkan_destroy_loader() {
  vkfl_destroy_loader(g_loader, NULL);
}


int main() {
  // Load libvulkan and retrieve a pointer to vkGetInstanceProcAddr.
  void* libvulkan = dlopen("libvulkan.so.1", RTLD_LAZY | RTLD_LOCAL);
  if (!libvulkan)
  {
    error("Failed to load libvulkan");
  }
  {
    PFN_vkGetInstanceProcAddr gipa = NULL;
    *((void**) &gipa) = dlsym(libvulkan, "vkGetInstanceProcAddr");
    if (!gipa)
    {
      error("Failed to retrieve \"vkGetInstanceProcAddr\" function pointer.");
    }
    vulkan_create_loader(gipa);
  }
  // Global Vulkan functions are valid at this point.

  // Retrieve instance version
  uint32_t instance_version = 0;
#if defined(VKFL_API_1_1_ENABLED) && VKFL_API_1_1_ENABLED
  VkResult res;
  if ((res = vkEnumerateInstanceVersion(&instance_version)) != VK_SUCCESS)
  {
    error("Failed to retrieve Vulkan instance version.");
  }
#else
  instance_version = VK_API_VERSION_1_0;
#endif
  printf("Vulkan Instance Version: v%d.%d.%d\n", VK_API_VERSION_MAJOR(instance_version),
          VK_API_VERSION_MINOR(instance_version), VK_API_VERSION_PATCH(instance_version));
  // Create Instance
  VkApplicationInfo app_info;
  memset(&app_info, 0, sizeof(VkApplicationInfo));
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app_info.apiVersion = VK_API_VERSION_1_1;
  VkInstanceCreateInfo instance_info;
  memset(&instance_info, 0, sizeof(VkInstanceCreateInfo));
  instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  instance_info.pApplicationInfo = &app_info;
  VkInstance instance;
  if ((res = vkCreateInstance(&instance_info, NULL, &instance)) != VK_SUCCESS)
  {
    error("Failed to create Vulkan instance.");
  }
  vulkan_load_instance(instance);
  // Instance level Vulkan functions are valid at this point.

  // Get the first physical device.
  VkPhysicalDevice physical_device;
  {
    uint32_t sz = 1 ;
    if ((res = vkEnumeratePhysicalDevices(instance, &sz, &physical_device)) < VK_SUCCESS)
    {
      error("Failed to retrieve Vulkan physical device.");
    }
  }
  // Get physical device properties.
  VkPhysicalDeviceProperties physical_device_properties;
  vkGetPhysicalDeviceProperties(physical_device, &physical_device_properties);
  printf("Vulkan Device Name: %s\n", physical_device_properties.deviceName);
  printf("Vulkan Device Version: v%d.%d.%d\n", VK_API_VERSION_MAJOR(physical_device_properties.apiVersion),
         VK_API_VERSION_MINOR(physical_device_properties.apiVersion),
         VK_API_VERSION_PATCH(physical_device_properties.apiVersion));
  // Create Vulkan device.
  VkDeviceCreateInfo device_info;
  memset(&device_info, 0, sizeof(VkDeviceCreateInfo));
  device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  VkDevice device;
  if ((res = vkCreateDevice(physical_device, &device_info, NULL, &device)) != VK_SUCCESS)
  {
    error("Failed to create Vulkan device.");
  }
  vulkan_load_device(device);
  // Device level Vulkan functions are valid at this point.

  // Clean up.
  vkDestroyDevice(device, NULL);
  vkDestroyInstance(instance, NULL);
  vulkan_destroy_loader();
  dlclose(libvulkan);
  return 0;
}
