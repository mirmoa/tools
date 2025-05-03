export default {
  root: 'src/frontend',
  base: './',
  build: {
    outDir: '../../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'src/frontend/index.html',
        coupang: 'src/frontend/coupang-ads.html'
      }
    }
  }
} 