import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

/**
 * Vite 插件：修复 @agentscope-ai/design 中 FileIcon 组件的 SVG ?import 问题。
 *
 * 该库使用 import icon from "./icons/xxx.svg?import" 语法，
 * 但 Vite 不识别 ?import 查询参数，将 .svg 当作图片返回 image/svg+xml MIME 类型，
 * 导致浏览器报 "Failed to load module script: Expected a JavaScript-or-Wasm module script"。
 *
 * 此插件拦截 .svg?import 请求，将 SVG 文件内容作为 JS 字符串模块返回。
 */
function svgImportPlugin() {
  return {
    name: 'svg-import-plugin',
    enforce: 'pre',
    resolveId(id, importer) {
      if (id.endsWith('.svg?import')) {
        // 解析为实际文件路径，让 Vite 能找到它
        const resolved = this.resolve(id.replace('?import', ''), importer, { skipSelf: true })
        return resolved
      }
      return null
    },
    load(id) {
      if (id.endsWith('.svg?import')) {
        const filePath = id.replace('?import', '')
        const svgContent = fs.readFileSync(filePath, 'utf-8')
        return `export default ${JSON.stringify(svgContent)}`
      }
      return null
    },
  }
}

export default defineConfig({
  define: {
    BASE_URL: JSON.stringify('/process'),
  },
  plugins: [react(), svgImportPlugin()],
  server: {
    port: 3000,
    proxy: {
      '/process': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  }
})
