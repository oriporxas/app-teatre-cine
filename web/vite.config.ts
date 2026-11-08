import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base './': la app funciona en cualquier dirección donde se publique.
export default defineConfig({
  base: './',
  plugins: [react()],
});
