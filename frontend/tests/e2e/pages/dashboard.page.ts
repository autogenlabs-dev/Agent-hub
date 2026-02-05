import { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Page elements
  get pageTitle(): Locator {
    return this.page.getByRole('heading', { name: /Dashboard/i });
  }

  get overViewText(): Locator {
    return this.page.getByText(/Overview of your agent communication channel/i);
  }

  get onlineAgentsCard(): Locator {
    return this.page.getByRole('region', { name: /Online Agents/i });
  }

  get pendingTasksCard(): Locator {
    return this.page.getByRole('region', { name: /Pending Tasks/i });
  }

  get recentMessagesCard(): Locator {
    return this.page.getByRole('region', { name: /Recent Messages/i });
  }

  get systemStatusCard(): Locator {
    return this.page.getByRole('region', { name: /System Status/i });
  }

  get onlineAgentsCount(): Locator {
    return this.onlineAgentsCard().getByRole('heading', { level: 2 });
  }

  get pendingTasksCount(): Locator {
    return this.pendingTasksCard().getByRole('heading', { level: 2 });
  }

  get recentMessagesCount(): Locator {
    return this.recentMessagesCard().getByRole('heading', { level: 2 });
  }

  get systemStatus(): Locator {
    return this.systemStatusCard().getByText(/Active/i);
  }

  get recentAgentsSection(): Locator {
    return this.page.getByRole('region', { name: /Recent Agents/i });
  }

  get recentAgentsCardTitle(): Locator {
    return this.recentAgentsSection().getByRole('heading', { level: 2 });
  }

  get recentTasksSection(): Locator {
    return this.page.getByRole('region', { name: /Recent Tasks/i });
  }

  get recentTasksCardTitle(): Locator {
    return this.recentTasksSection().getByRole('heading', { level: 2 });
  }

  get agentsLink(): Locator {
    return this.page.getByRole('link', { name: /agents/i });
  }

  get tasksLink(): Locator {
    return this.page.getByRole('link', { name: /tasks/i });
  }

  get messagesLink(): Locator {
    return this.page.getByRole('link', { name: /messages/i });
  }
}