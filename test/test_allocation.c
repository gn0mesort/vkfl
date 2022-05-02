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
#include <stdlib.h>

#include <vulkan/vulkan.h>

#include "vkfl.h"

int main() {
  struct vkfl_allocation_callbacks alloc;
  alloc.allocator = malloc;
  alloc.deallocator = free;
  struct vkfl_loader* ld = vkfl_create_loader(vkGetInstanceProcAddr, &alloc);
  assert(ld != NULL);
  assert(vkfl_get(ld, VKFL_COMMAND_EnumerateInstanceExtensionProperties) != NULL);
  struct vkfl_loader* copy_ld = vkfl_copy_loader(ld, &alloc);
  assert(copy_ld != NULL);
  assert(vkfl_get(copy_ld, VKFL_COMMAND_EnumerateInstanceExtensionProperties) != NULL);
  {
    PFN_vkVoidFunction a = vkfl_get(ld, VKFL_COMMAND_EnumerateInstanceExtensionProperties);
    PFN_vkVoidFunction b = vkfl_get(copy_ld, VKFL_COMMAND_EnumerateInstanceExtensionProperties);
    assert(a == b);
  }
  vkfl_destroy_loader(ld, &alloc);
  vkfl_destroy_loader(copy_ld, &alloc);
  return 0;
}
