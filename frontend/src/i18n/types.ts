export type Language = "en" | "vi" | "zh";

export interface TranslationDictionary {
  common: {
    home: string;
    overview: string;
    search: string;
    searchPlaceholder: string;
    add: string;
    addNew: string;
    export: string;
    exportCsv: string;
    delete: string;
    deleteSelected: string;
    deleteConfirm: string;
    bulkDeleteConfirm: string;
    deselect: string;
    selectedCount: string;
    save: string;
    cancel: string;
    edit: string;
    view: string;
    viewOrEdit: string;
    deleteRecord: string;
    actions: string;
    loading: string;
    loadingData: string;
    loadingSchema: string;
    error: string;
    schemaError: string;
    noDataFound: string;
    noRecordsMatch: string;
    clearFilters: string;
    filters: string;
    advancedFilters: string;
    applyFilters: string;
    reset: string;
    total: string;
    showingRecords: string;
    previous: string;
    next: string;
    refresh: string;
    status: string;
    nameOrId: string;
    creation: string;
    modified: string;
    records: string;
    switchWorkspace: string;
    goBack: string;
  };
  sort: {
    sortBy: string;
    newest: string;
    oldest: string;
    recentlyModified: string;
    nameAsc: string;
    nameDesc: string;
    ascending: string;
    descending: string;
  };
  filter: {
    title: string;
    subtitle: string;
    field: string;
    operator: string;
    value: string;
    addCondition: string;
    removeCondition: string;
    operators: {
      equals: string;
      notEquals: string;
      like: string;
      in: string;
      greaterThan: string;
      lessThan: string;
      greaterOrEqual: string;
      lessOrEqual: string;
    };
  };
  sidebar: {
    overview: string;
    masters: string;
    transactions: string;
    reports: string;
    otherSettings: string;
    customization: string;
    loadingMenu: string;
  };
  workspace: {
    popularAndOverview: string;
    dashboard: string;
    noWorkspaceFound: string;
    manageAndLookUp: string;
  };
  report: {
    title: string;
    subtitle: string;
    company: string;
    fiscalYear: string;
    fromDate: string;
    toDate: string;
    filterResults: string;
    refreshData: string;
    loadingReport: string;
    noTransactions: string;
    reportError: string;
  };
  pos: {
    title: string;
    subtitle: string;
    profiles: string;
    totalInvoices: string;
    openShift: string;
    newInvoice: string;
    createInvoice: string;
    posProfilesList: string;
    addProfile: string;
    noProfilesFound: string;
    warehouse: string;
    priceList: string;
    registeredRegisters: string;
    issuedInvoices: string;
  };
  funnel: {
    title: string;
    subtitle: string;
    activeLeads: string;
    opportunities: string;
    quotations: string;
    converted: string;
    overallConversionRate: string;
    retentionRate: string;
    records: string;
    addLead: string;
    addOpportunity: string;
    conversionFlow: string;
  };
  permissions: {
    title: string;
    subtitle: string;
    doctype: string;
    role: string;
    rolePermissionsFor: string;
    viewDocTypeStructure: string;
  };
  copilot: {
    title: string;
    subtitle: string;
    askMeAnything: string;
    send: string;
    placeholder: string;
    suggestedPrompts: string;
  };
  auth: {
    login: string;
    email: string;
    password: string;
    loggingIn: string;
    loginFailed: string;
    welcomeBack: string;
    enterCredentials: string;
    rememberMe: string;
    forgotPassword: string;
  };
}

