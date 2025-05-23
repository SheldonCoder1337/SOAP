<template>
  <div class="database-container layout-container" v-if="configStore.config.enable_knowledge_base">
    <HeaderComponent
      :title="$t('database_header_title')"
      :description="$t('database_header_desc')"
    >
      <template #actions>
        <a-button type="primary" @click="newDatabase.open=true">{{$t('"create_new_database"')}}</a-button>
      </template>
    </HeaderComponent>

    <a-modal :open="newDatabase.open" title="new database" @ok="createDatabase">
      <h3>{{$t('DB_name')}}<span style="color: var(--error-color)">*</span></h3>
      <a-input v-model:value="newDatabase.name" placeholder="new database name" />
      <h3 style="margin-top: 20px;">{{$t('DB_desc')}}</h3>
      <a-textarea
        v-model:value="newDatabase.description"
        placeholder="new database description"
        :auto-size="{ minRows: 2, maxRows: 5 }"
      />
      <!-- <h3 style="margin-top: 20px;">向量维度</h3>
      <p>必须与向量模型 {{ configStore.config.embed_model }} 一致</p>
      <a-input v-model:value="newDatabase.dimension" placeholder="向量维度 (e.g. 768, 1024)" /> -->
      <template #footer>
        <a-button key="back" @click="newDatabase.open=false">{{$t('cancel')}}</a-button>
        <a-button key="submit" type="primary" :loading="newDatabase.loading" @click="createDatabase">{{$t('create')}}</a-button>
      </template>
    </a-modal>
    <div class="databases">
      <div class="new-database dbcard" @click="newDatabase.open=true">
        <div class="top">
          <div class="icon"><PlusOutlined /></div>
          <div class="info">
            <h3>{{$t('create_new_database')}}</h3>
          </div>
        </div>
        <p>{{$t('create_new_database_msg')}}</p>
      </div>
      <div
        v-for="database in databases"
        :key="database.db_id"
        class="database dbcard"
        @click="navigateToDatabase(database.db_id)">
        <div class="top">
          <div class="icon"><ReadFilled /></div>
          <div class="info">
            <h3>{{ database.name }}</h3>
            <p><span>{{ database.metaname }}</span> · <span>{{ database.metadata.row_count }}行</span></p>
          </div>
        </div>
        <p class="description">{{ database.description || 'none' }}</p>
        <div class="tags">
          <a-tag color="blue" v-if="database.embed_model">{{ database.embed_model }}</a-tag>
          <a-tag color="green" v-if="database.dimension">{{ database.dimension }}</a-tag>
        </div>
        <!-- <button @click="deleteDatabase(database.collection_name)">删除</button> -->
      </div>
    </div>
    <!-- <h2>图数据库 &nbsp; <a-spin v-if="graphloading" :indicator="indicator" /></h2>
    <p>基于 neo4j 构建的图数据库。</p>
    <div :class="{'graphloading': graphloading, 'databases': true}" v-if="graph">
      <div class="dbcard graphbase" @click="navigateToGraph">
        <div class="top">
          <div class="icon"><AppstoreFilled /></div>
          <div class="info">
            <h3>{{ graph?.database_name }}</h3>
            <p>
              <span>{{ graph?.status }}</span> ·
              <span>{{ graph?.entity_count }}实体</span>
            </p>
          </div>
        </div>
        <p class="description">基于 neo4j 构建的图数据库。基于 neo4j 构建的图数据库。基于 neo4j 构建的图数据库。</p>
      </div>
    </div> -->
  </div>
  <div class="database-empty" v-else>
    <a-empty>
      <template #description>
        <span>
          {{$t('Go_to')}} <router-link to="/setting" style="color: var(--main-color); font-weight: bold;">{{$t('settings')}}</router-link> {{$t('configure_knowledgebase')}}。
        </span>
      </template>
    </a-empty>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router';
import { message, Button } from 'ant-design-vue'
import { ReadFilled, PlusOutlined, AppstoreFilled, LoadingOutlined } from '@ant-design/icons-vue'
import { useConfigStore } from '@/stores/config';
import HeaderComponent from '@/components/HeaderComponent.vue';

const route = useRoute()
const router = useRouter()
const databases = ref([])
const graph = ref(null)
const graphloading = ref(false)

const indicator = h(LoadingOutlined, {spin: true});
const configStore = useConfigStore()

const newDatabase = reactive({
  name: '',
  description: '',
  dimension: '',
  loading: false,
})

const loadDatabases = () => {
  // loadGraph()
  fetch('/api/data/', {
    method: "GET",
  })
    .then(response => response.json())
    .then(data => {
      console.log(data)
      databases.value = data.databases
    }
  )
}

const createDatabase = () => {
  newDatabase.loading = true
  console.log(newDatabase)
  if (!newDatabase.name) {
    message.error('数据库名称不能为空')
    newDatabase.loading = false
    return
  }
  fetch('/api/data/', {
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      database_name: newDatabase.name,
      description: newDatabase.description,
      db_type: "knowledge",
      dimension: newDatabase.dimension ? parseInt(newDatabase.dimension) : null,
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log(data)
    loadDatabases()
    newDatabase.open = false
    newDatabase.name = ''
    newDatabase.description = '',
    newDatabase.dimension = ''
  })
  .finally(() => {
    newDatabase.loading = false
  })
}

const navigateToDatabase = (databaseId) => {
  router.push({ path: `/database/${databaseId}` });
};

const navigateToGraph = () => {
  router.push({ path: `/database/graph` });
};

watch(() => route.path, (newPath, oldPath) => {
  if (newPath === '/database') {
    loadDatabases();
  }
});

onMounted(() => {
  loadDatabases()
})

</script>

<style lang="less" scoped>
.database-actions, .document-actions {
  margin-bottom: 20px;
}
.databases {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;

  .new-database {
    background-color: #F0F3F4;
  }
}

.database, .graphbase {
  background-color: white;
  box-shadow: 0px 1px 2px 0px rgba(16,24,40,.06),0px 1px 3px 0px rgba(16,24,40,.1);
  border: 2px solid white;
  transition: box-shadow 0.2s ease-in-out;

  &:hover {
    box-shadow: 0px 4px 6px -2px rgba(16,24,40,.03),0px 12px 16px -4px rgba(16,24,40,.08);
  }
}

.dbcard, .database {
  width: 100%;
  padding: 10px;
  border-radius: 12px;
  height: 160px;
  padding: 20px;
  cursor: pointer;

  .top {
    display: flex;
    align-items: center;
    height: 50px;
    margin-bottom: 10px;

    .icon {
      width: 50px;
      height: 50px;
      font-size: 28px;
      margin-right: 10px;
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: #F5F8FF;
      border-radius: 8px;
      border: 1px solid #E0EAFF;
      color: var(--main-color);
    }

    .info {
      h3, p {
        margin: 0;
        color: black;
      }

      h3 {
        font-size: 16px;
        font-weight: bold;
      }

      p {
        color: var(--gray-900);
        font-size: small;
      }
    }
  }

  .description {
    color: var(--gray-900);
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
    margin-bottom: 10px;
  }
}

// 整个卡片是模糊的
// .graphloading {
//   filter: blur(2px);
// }

.database-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  flex-direction: column;
  color: var(--gray-900);
}

.database-container {
  padding: 0;
}
</style>
