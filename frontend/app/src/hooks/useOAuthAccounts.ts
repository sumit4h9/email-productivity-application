import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  oauthAPI,
  AccountListResponse,
  AccountStatusResponse,
  DisconnectResponse,
} from "@/lib/api";

// Hook to fetch connected accounts list
export const useConnectedAccounts = () => {
  return useQuery<AccountListResponse>({
    queryKey: ["connectedAccounts"],
    queryFn: () => oauthAPI.listAccounts(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

// Hook to fetch account status by account ID
export const useAccountStatus = (accountId: string) => {
  return useQuery<AccountStatusResponse>({
    queryKey: ["accountStatus", accountId],
    queryFn: () => oauthAPI.getAccountStatus(accountId),
    enabled: !!accountId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

// Hook to disconnect an account by account ID
export const useDisconnectAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: string) => oauthAPI.disconnectAccount(accountId),
    onSuccess: () => {
      // Invalidate connected accounts list to refetch updated data
      queryClient.invalidateQueries({ queryKey: ["connectedAccounts"] });
    },
  });
};
