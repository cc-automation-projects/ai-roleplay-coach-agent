import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: {
      target: `${process.env.VITE_API_URL || 'http://localhost:8000'}/openapi.json`,
      validation: false,
    },
    output: {
      target: './src/shared/api/generated.ts',
      client: 'react-query',
      httpClient: 'axios',
      headers: true,
      override: {
        mutator: './src/shared/api/client.ts',
        query: {
          useQuery: true,
          useInfinite: false,
          useMutation: true,
        },
      },
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
});
