This optional app is excluded from the core image. Installing it requires ERPNext,
Lotus Fin and an explicit boolean site setting `lotus_erpnext_integration_qualified`.
This is an operational qualification flag, not a user permission grant. Legacy
routes still require authentication and their own company/resource authorization.
Existing legacy guest decorators remain source history; core denies those routes
before import. This optional integration has not received business/security acceptance.
