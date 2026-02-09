/**
 * Environment variable type definitions for AgriScheme mobile app
 */

declare namespace NodeJS {
  interface ProcessEnv {
    // Production: Individual service URLs
    EXPO_PUBLIC_AUTH_URL?: string;
    EXPO_PUBLIC_FARMER_URL?: string;
    EXPO_PUBLIC_FARM_URL?: string;
    EXPO_PUBLIC_GIS_URL?: string;
    EXPO_PUBLIC_FINANCIAL_URL?: string;
    EXPO_PUBLIC_MARKET_URL?: string;
    EXPO_PUBLIC_AI_URL?: string;
    EXPO_PUBLIC_IOT_URL?: string;
    EXPO_PUBLIC_LIVESTOCK_URL?: string;
    EXPO_PUBLIC_TASK_URL?: string;
    EXPO_PUBLIC_INVENTORY_URL?: string;
    EXPO_PUBLIC_NOTIFICATION_URL?: string;
    EXPO_PUBLIC_TRACEABILITY_URL?: string;
    EXPO_PUBLIC_COMPLIANCE_URL?: string;
    EXPO_PUBLIC_INTEGRATION_URL?: string;

    // Alternative: Unified API gateway URL (when available)
    EXPO_PUBLIC_API_URL?: string;

    // Server IP (reference)
    SERVER_IP?: string;
  }
}
