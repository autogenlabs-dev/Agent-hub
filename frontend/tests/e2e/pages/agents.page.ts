import { Page, Locator } from '@playwright/test';

export class AgentsPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Page elements
  get pageTitle(): Locator {
    return this.page.getByRole('heading', { name: /Agents/i });
  }

  get overviewText(): Locator {
    return this.page.getByText(/Monitor and manage your connected agents/i);
  }

  get totalAgentsCard(): Locator {
    return this.page.getByRole('region', { name: /Total Agents/i });
  }

  get onlineCard(): Locator {
    return this.page.getByRole('region', { name: /Online/i });
  }

  get offlineCard(): Locator {
    return this.page.getByRole('region', { name: /Offline/i });
  }

  get agentTypesCard(): Locator {
    return this.page.getByRole('region', { name: /Agent Types/i });
  }

  get onlineAgentsCount(): Locator {
    return this.onlineCard().getByRole('heading', { level: 2 });
  }

  get offlineAgentsCount(): Locator {
    return this.offlineCard().getByRole('heading', { level: 2 });
  }

  get agentTypesCount(): Locator {
    return this.agentTypesCard().getByRole('heading', { level: 2 });
  }

  get onlineAgentsSection(): Locator {
    return this.page.getByRole('region', { name: /Online Agents/i });
  }

  get onlineAgentsCardTitle(): Locator {
    return this.onlineAgentsSection().getByRole('heading', { level: 2 });
  }

  get allAgentsSection(): Locator {
    return this.page.getByRole('region', { name: /All Agents/i });
  }

  get allAgentsCardTitle(): Locator {
    return this.allAgentsSection().getByRole('heading', { level: 2 });
  }

  get allAgentsList(): Locator {
    return this.allAgentsSection().locator('.space-y-3 > div');
  }

  get dashboardLink(): Locator {
    return this.page.getByRole('link', { name: /dashboard/i });
  }
}