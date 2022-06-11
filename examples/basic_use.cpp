/**
 * Copyright 2021 Alexander Rothman
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
#include <cinttypes>

#include <iostream>
#include <stdexcept>

#include <vulkan/vulkan.h>

#include "vkfl.hpp"

int main() {
  try
  {
    // Create a loader and load global function pointers.
    auto ld = vkfl::loader{ vkGetInstanceProcAddr };
    auto app_info = VkApplicationInfo{ };
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.apiVersion = VK_VERSION_1_2;
    auto instance_info = VkInstanceCreateInfo{ };
    instance_info.sType = VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO;
    instance_info.pApplicationInfo = &app_info;
    // Resolve a function pointer.
    // Note that to do anything useful with the resulting function pointer it needs to be cast to the correct type.
    // vkfl.hpp does not introduce these types so you need vulkan.h as well.
    auto create_instance = reinterpret_cast<PFN_vkCreateInstance>(ld(vkfl::command::vkCreateInstance));
    if (!create_instance)
    {
      throw std::runtime_error{ "Failed to load \"vkCreateInstance\"." };
    }
    auto instance = VkInstance{ };
    auto res = create_instance(&instance_info, nullptr, &instance);
    if (res != VK_SUCCESS)
    {
      throw std::runtime_error{ "Failed to create Vulkan instance." };
    }
    // Update the loader with instance function pointers.
    ld.load(instance);
    auto enumerate_physical_devices =
      reinterpret_cast<PFN_vkEnumeratePhysicalDevices>(ld(vkfl::command::vkEnumeratePhysicalDevices));
    if (!enumerate_physical_devices)
    {
      throw std::runtime_error{ "Failed to load \"vkEnumeratePhysicalDevices\"." };
    }
    auto sz = std::uint32_t{ 1 };
    auto pdev = VkPhysicalDevice{ };
    res = enumerate_physical_devices(instance, &sz, &pdev);
    if (res < VK_SUCCESS)
    {
      throw std::runtime_error{ "Failed to enumerate Vulkan physical devices." };
    }
    auto device_info = VkDeviceCreateInfo{ };
    device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    auto create_device = reinterpret_cast<PFN_vkCreateDevice>(ld(vkfl::command::vkCreateDevice));
    if (!create_device)
    {
      throw std::runtime_error{ "Failed to load \"vkCreateDevice\"." };
    }
    auto device = VkDevice{ };
    res = create_device(pdev, &device_info, nullptr, &device);
    if (res != VK_SUCCESS)
    {
      throw std::runtime_error{ "Failed to create Vulkan device." };
    }
    // Update the loader with device function pointers.
    ld.load(device);
    std::cout << "Successfully created Vulkan environment!" << std::endl;
    auto destroy_device = reinterpret_cast<PFN_vkDestroyDevice>(ld(vkfl::command::vkDestroyDevice));
    if (!destroy_device)
    {
      throw std::runtime_error{ "Failed to load \"vkDestroyDevice\"." };
    }
    destroy_device(device, nullptr);
    // After destroying the loaded device you may wish to clear the corresponding function pointers.
    // This will reload the instance function pointers in place of device pointers.
    ld.unload_device();
    auto destroy_instance = reinterpret_cast<PFN_vkDestroyInstance>(ld(vkfl::command::vkDestroyInstance));
    if (!destroy_instance)
    {
      throw std::runtime_error{ "Failed to load \"vkDestroyInstance\"." };
    }
    destroy_instance(instance, nullptr);
    // As with the device, instance function pointers can be cleared.
    // This reverts the entire loader to the state it was in just after construction.
    ld.unload_instance();
    std::cout << "Successfully destroyed Vulkan environment!" << std::endl;
  }
  catch (const std::exception& err)
  {
    std::cerr << err.what() << std::endl;
    return 1;
  }
  return 0;
}
