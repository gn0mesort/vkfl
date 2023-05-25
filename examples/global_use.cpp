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
#include <cinttypes>

#include <memory>
#include <stdexcept>
#include <iostream>

#include "vkfl.hpp"
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
  reinterpret_cast<PFN_##cmd>(g_loader->get(vkfl::command::cmd))

// Define command function macros. This could be done by a script to generate macros for all enabled functions.
#define vkGetInstanceProcAddr VK_GET_PFN(vkGetInstanceProcAddr)
#define vkEnumerateInstanceVersion VK_GET_PFN(vkEnumerateInstanceVersion)
#define vkCreateInstance VK_GET_PFN(vkCreateInstance)
#define vkDestroyInstance VK_GET_PFN(vkDestroyInstance)
#define vkEnumeratePhysicalDevices VK_GET_PFN(vkEnumeratePhysicalDevices)
#define vkGetPhysicalDeviceProperties VK_GET_PFN(vkGetPhysicalDeviceProperties)
#define vkCreateDevice VK_GET_PFN(vkCreateDevice)
#define vkDestroyDevice VK_GET_PFN(vkDestroyDevice)

// Due to using dlopen the vkfl::loader can't be initialized statically (as it requires a valid pointer to
// vkGetInstanceProcAddr during construction). An alternative to this would be to declare the prototype for
// vkGetInstanceProcAddr yourself prior to declaring the loader.
std::unique_ptr<vkfl::loader> g_loader{ };

// Functions to load each level of Vulkan functionality.
void vulkan_load(const PFN_vkGetInstanceProcAddr gipa) {
  g_loader.reset(new vkfl::loader{ gipa });
}

void vulkan_load(const VkInstance instance) {
  g_loader->load(instance);
}

void vulkan_load(const VkDevice device) {
  g_loader->load(device);
}

int main() {
  try
  {
    // Load libvulkan and retrieve a pointer to vkGetInstanceProcAddr.
    auto libvulkan = dlopen("libvulkan.so.1", RTLD_LAZY | RTLD_LOCAL);
    if (!libvulkan)
    {
      throw std::runtime_error{ "Failed to load libvulkan" };
    }
    {
      auto gipa = PFN_vkGetInstanceProcAddr{ };
      *reinterpret_cast<void**>(&gipa) = dlsym(libvulkan, "vkGetInstanceProcAddr");
      if (!gipa)
      {
        throw std::runtime_error{ "Failed to retrieve \"vkGetInstanceProcAddr\" function pointer." };
      }
      vulkan_load(gipa);
    }
    // Global Vulkan functions are valid at this point.

    // Retrieve instance version
    auto instance_version = std::uint32_t{ 0 };
#if VKFL_API_VK_VERSION_1_1_ENABLED
    if (auto res = vkEnumerateInstanceVersion(&instance_version); res != VK_SUCCESS)
    {
      throw std::runtime_error{ "Failed to retrieve Vulkan instance version." };
    }
#else
    instance_version = VK_API_VERSION_1_0;
#endif
    std::cout << "Vulkan Instance Version: v" << VK_API_VERSION_MAJOR(instance_version);
    std::cout << "." << VK_API_VERSION_MINOR(instance_version) << "." << VK_API_VERSION_PATCH(instance_version);
    std::cout << std::endl;
    // Create Instance
    auto app_info = VkApplicationInfo{ };
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.apiVersion = VK_API_VERSION_1_1;
    auto instance_info = VkInstanceCreateInfo{ };
    instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    instance_info.pApplicationInfo = &app_info;
    auto instance = VkInstance{ };
    if (auto res = vkCreateInstance(&instance_info, nullptr, &instance); res != VK_SUCCESS)
    {
      throw std::runtime_error{ "Failed to create Vulkan instance." };
    }
    vulkan_load(instance);
    // Instance level Vulkan functions are valid at this point.

    // Get the first physical device.
    auto physical_device = VkPhysicalDevice{ };
    {
      auto sz = std::uint32_t{ 1 };
      if (auto res = vkEnumeratePhysicalDevices(instance, &sz, &physical_device); res < VK_SUCCESS)
      {
        throw std::runtime_error{ "Failed to retrieve Vulkan physical device." };
      }
    }
    // Get physical device properties.
    auto physical_device_properties = VkPhysicalDeviceProperties{ };
    vkGetPhysicalDeviceProperties(physical_device, &physical_device_properties);
    std::cout << "Vulkan Device Name: " << physical_device_properties.deviceName << std::endl;
    std::cout << "Vulkan Device Version: v" << VK_API_VERSION_MAJOR(physical_device_properties.apiVersion);
    std::cout << "." << VK_API_VERSION_MINOR(physical_device_properties.apiVersion);
    std::cout << "." << VK_API_VERSION_PATCH(physical_device_properties.apiVersion) << std::endl;
    // Create Vulkan device.
    auto device_info = VkDeviceCreateInfo{ };
    device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    auto device = VkDevice{ };
    if (auto res = vkCreateDevice(physical_device, &device_info, nullptr, &device); res != VK_SUCCESS)
    {
      throw std::runtime_error{ "Failed to create Vulkan device." };
    }
    vulkan_load(device);
    // Device level Vulkan functions are valid at this point.

    // Clean up.
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);
    dlclose(libvulkan);
  }
  catch (const std::exception& err)
  {
    std::cerr << err.what() << std::endl;
    return 1;
  }
  return 0;
}
