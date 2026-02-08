<template>
  <div class="section-list">
    <draggable
      v-model="localSections"
      item-key="id"
      handle=".drag-handle"
      @end="onDragEnd"
    >
      <template #item="{ element }">
        <div :style="{ paddingLeft: (element.depth_level || 0) * 24 + 'px' }">
          <SectionCard
            :section="element"
            @click="$emit('click', element)"
            @edit="$emit('edit', element)"
            @delete="$emit('delete', element)"
          />
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import draggable from 'vuedraggable'
import SectionCard from './SectionCard.vue'

const props = defineProps({
  sections: { type: Array, default: () => [] }
})

const emit = defineEmits(['click', 'edit', 'delete', 'reorder'])

const localSections = ref([...props.sections])

watch(() => props.sections, (val) => {
  localSections.value = [...val]
}, { deep: true })

function onDragEnd() {
  const items = localSections.value.map((s, index) => ({
    id: s.id,
    sort_order: index
  }))
  emit('reorder', items)
}
</script>
