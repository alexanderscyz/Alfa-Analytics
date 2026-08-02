export type CloudAccount = {
  id: string;
  name: string;
  provider: string;
  aws_account_id: string;
  role_arn: string;
  external_id: string | null;
  status: string;
  last_sync_at: string | null;
  last_sync_region: string | null;
  last_sync_status: string | null;
  resource_count: number;
};