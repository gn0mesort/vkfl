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
#include <stddef.h>
#include <string.h>

#include <vulkan/vulkan.h>

#include "vkfl.h"

#define VKFL_GET_PFN(ld, cmd) ((PFN_vk##cmd) vkfl_get(ld, VKFL_COMMAND_##cmd))

int main() {
  struct vkfl_loader* ld = vkfl_create_loader(vkGetInstanceProcAddr, NULL);
  assert(ld != NULL);
  VkApplicationInfo app_info;
  memset(&app_info, 0, sizeof(VkApplicationInfo));
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
  VkInstanceCreateInfo instance_info;
  memset(&instance_info, 0, sizeof(VkInstanceCreateInfo));
  instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  instance_info.pApplicationInfo = &app_info;
  VkInstance instance;
  {
    PFN_vkCreateInstance pfn = VKFL_GET_PFN(ld, CreateInstance);
    assert(pfn != NULL);
    VkResult res = pfn(&instance_info, NULL, &instance);
    assert(res == VK_SUCCESS);
    (void) res;
  }
  assert(vkfl_load_instance(ld, instance) >= 0);
  assert(VKFL_GET_PFN(ld, GetDeviceProcAddr) != NULL);
  assert(VKFL_GET_PFN(ld, GetDeviceQueue) != NULL);
  {
    PFN_vkDestroyInstance pfn = VKFL_GET_PFN(ld, DestroyInstance);
    assert(pfn != NULL);
    pfn(instance, NULL);
  }
  vkfl_destroy_loader(ld, NULL);
  return 0;
}
