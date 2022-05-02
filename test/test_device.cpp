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
#include <cassert>
#include <cinttypes>
#include <cstring>

#include <vulkan/vulkan.h>

#include "vkfl.hpp"

#define VKFL_GET_PFN(ld, cmd) (reinterpret_cast<PFN_vk##cmd>(ld(vkfl::command::cmd)))

int main() {
  auto ld = vkfl::loader{ vkGetInstanceProcAddr };
  auto app_info = VkApplicationInfo{ };
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
#if VKFL_API_1_3_ENABLED
  app_info.apiVersion = VK_API_VERSION_1_3;
#elif VKFL_API_1_2_ENABLED
  app_info.apiVersion = VK_API_VERSION_1_2;
#elif VKFL_API_1_1_ENABLED
  app_info.apiVersion = VK_API_VERSION_1_1;
#else
  app_info.apiVersion = VK_API_VERSION_1_0;
#endif
  auto instance_info = VkInstanceCreateInfo{ };
  instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  instance_info.pApplicationInfo = &app_info;
  auto instance = VkInstance{ };
  {
    auto pfn = VKFL_GET_PFN(ld, CreateInstance);
    assert(pfn != nullptr);
    auto res = pfn(&instance_info, nullptr, &instance);
    assert(res == VK_SUCCESS);
    (void) res;
  }
  ld.load(instance);
  auto device_info = VkDeviceCreateInfo{ };
  device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  auto pdev = VkPhysicalDevice{ };
  {
    auto pfn = VKFL_GET_PFN(ld, EnumeratePhysicalDevices);
    assert(pfn != nullptr);
    auto sz = std::uint32_t{ 1 };
    auto res = pfn(instance, &sz, &pdev);
    assert(res >= 0);
    (void) res;
  }
  auto device = VkDevice{ };
  {
    auto pfn = VKFL_GET_PFN(ld, CreateDevice);
    assert(pfn != nullptr);
    auto res = pfn(pdev, &device_info, nullptr, &device);
    assert(res == VK_SUCCESS);
    (void) res;
  }
  auto old_pfn = VKFL_GET_PFN(ld, CmdDraw);
  ld.load(device);
  auto new_pfn = VKFL_GET_PFN(ld, CmdDraw);
  assert(new_pfn != nullptr);
  assert(new_pfn != old_pfn);
  (void) old_pfn;
  (void) new_pfn;
  {
    auto pfn = VKFL_GET_PFN(ld, DestroyDevice);
    assert(pfn != nullptr);
    pfn(device, nullptr);
  }
  {
    auto pfn = VKFL_GET_PFN(ld, DestroyInstance);
    assert(pfn != nullptr);
    pfn(instance, nullptr);
  }
  return 0;
}
