module.exports = {
  apps: [
    {
      name: 'lead-hunter-service',
      script: './scripts/scheduler.js',
      env: {
        NODE_ENV: 'production',
        REVENUE_GOAL: '2000'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      log_date_format: 'YYYY-MM-DD HH:mm Z'
    }
  ]
};
