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
#include <stdlib.h>
#include <assert.h>

#include <vulkan/vulkan.h>

#include "vkfl.h"

#define VKFL_GET_PFN(ld, cmd) ((PFN_vk##cmd) vkfl_get(ld, VKFL_COMMAND_##cmd))

int main() {
  struct vkfl_loader* ld = vkfl_create_loader(vkGetInstanceProcAddr, NULL);
  assert(VKFL_GET_PFN(ld, CreateInstance) != NULL);
  vkfl_destroy_loader(ld, NULL);
  return 0;
}
