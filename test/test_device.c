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
#include <assert.h>
#include <inttypes.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

#include <vulkan/vulkan.h>

#include "vkfl.h"

#define VKFL_GET_PFN(ld, cmd) ((PFN_##cmd) vkfl_get(ld, VKFL_COMMAND_##cmd))

int main(void) {
  struct vkfl_loader* ld = vkfl_create_loader(vkGetInstanceProcAddr, NULL);
  assert(ld != NULL);
  VkApplicationInfo app_info;
  memset(&app_info, 0, sizeof(VkApplicationInfo));
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
#if VKFL_API_VK_VERSION_1_3_ENABLED
  app_info.apiVersion = VK_API_VERSION_1_3;
#elif VKFL_API_VK_VERSION_1_2_ENABLED
  app_info.apiVersion = VK_API_VERSION_1_2;
#elif VKFL_API_VK_VERSION_1_1_ENABLED
  app_info.apiVersion = VK_API_VERSION_1_1;
#else
  app_info.apiVersion = VK_API_VERSION_1_0;
#endif
  VkInstanceCreateInfo instance_info;
  memset(&instance_info, 0, sizeof(VkInstanceCreateInfo));
  instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  instance_info.pApplicationInfo = &app_info;
  VkInstance instance;
  {
    PFN_vkCreateInstance pfn = VKFL_GET_PFN(ld, vkCreateInstance);
    assert(pfn != NULL);
    VkResult res = pfn(&instance_info, NULL, &instance);
    assert(res == VK_SUCCESS);
    (void) res;
  }
  vkfl_load_instance(ld, instance);
  VkDeviceCreateInfo device_info;
  memset(&device_info, 0, sizeof(VkDeviceCreateInfo));
  device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  VkPhysicalDevice* pdevs = NULL;
  uint32_t sz = 0;
  {
    PFN_vkEnumeratePhysicalDevices pfn = VKFL_GET_PFN(ld, vkEnumeratePhysicalDevices);
    assert(pfn != NULL);
    VkResult res = pfn(instance, &sz, NULL);
    assert(res >= 0);
    (void) res;
    pdevs = malloc(sz * sizeof(VkPhysicalDevice));
    assert(pdevs != NULL);
    res = pfn(instance, &sz, pdevs);
    assert(res >= 0);
    (void) res;
  }
  // Try to select a discrete device if available.
  // This is to avoid lavapipe.
  VkPhysicalDevice pdev = VK_NULL_HANDLE;
  {
    PFN_vkGetPhysicalDeviceProperties pfn = VKFL_GET_PFN(ld, vkGetPhysicalDeviceProperties);
    assert(pfn != NULL);
    VkPhysicalDeviceProperties properties;
    for (uint32_t i = 0; i < sz; ++i)
    {
      vkGetPhysicalDeviceProperties(pdevs[i], &properties);
      if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU)
      {
        pdev = pdevs[i];
      }
    }
    if (pdev == VK_NULL_HANDLE)
    {
      pdev = pdevs[0];
    }
    free(pdevs);
    pdevs = NULL;
  }
  VkDevice device;
  {
    PFN_vkCreateDevice pfn = VKFL_GET_PFN(ld, vkCreateDevice);
    assert(pfn != NULL);
    VkResult res = pfn(pdev, &device_info, NULL, &device);
    assert(res == VK_SUCCESS);
    (void) res;
  }
  PFN_vkCmdDraw old_pfn = VKFL_GET_PFN(ld, vkCmdDraw);
  vkfl_load_device(ld, device);
  PFN_vkCmdDraw new_pfn = VKFL_GET_PFN(ld, vkCmdDraw);
  assert(new_pfn != NULL);
  assert(new_pfn != old_pfn);
  (void) old_pfn;
  (void) new_pfn;
  {
    PFN_vkDestroyDevice pfn = VKFL_GET_PFN(ld, vkDestroyDevice);
    assert(pfn != NULL);
    pfn(device, NULL);
  }
  {
    PFN_vkDestroyInstance pfn = VKFL_GET_PFN(ld, vkDestroyInstance);
    assert(pfn != NULL);
    pfn(instance, NULL);
  }
  vkfl_destroy_loader(ld, NULL);
  return 0;
}
