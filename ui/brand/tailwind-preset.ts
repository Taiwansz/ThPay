import type { Config } from 'tailwindcss';

const thpayPreset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        thp: {
          ink: '#101A44',
          cobalt: '#2F66F3',
          solar: '#FFC83D',
          mint: '#8FE1CF',
          blush: '#F7A7B8',
          coral: '#FF7D72',
          ivory: '#FFF9F1',
          paper: '#F6F2EC',
          line: '#E5DED5',
          muted: '#64708A',
        },
      },
      borderRadius: { thp: '16px', 'thp-lg': '20px', 'thp-xl': '24px' },
      fontFamily: { sans: ['Plus Jakarta Sans', 'Inter', 'Segoe UI', 'Arial', 'sans-serif'] },
      transitionTimingFunction: { thp: 'cubic-bezier(.16,1,.3,1)' },
    },
  },
};

export default thpayPreset;
