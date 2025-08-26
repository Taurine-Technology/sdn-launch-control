# Bridge Components

This directory contains components for managing bridges in the SDN Launch Control system.

## Components

### BridgeDataComponent

Main component for displaying and managing bridges for a device.

**Features:**

- Display bridge information (name, DPID, ports)
- Add new bridges
- Delete existing bridges
- Loading states and error handling
- Toast notifications for user feedback

**Props:**

```tsx
interface BridgeDataComponentProps {
  isLoading: boolean;
  bridgeData: BridgeApiResponse | null;
  getBridgeData: (lanIpAddress: string) => Promise<void>;
  deviceIp: string;
}
```

### AddBridgeDialog

Dialog component for adding new bridges to a device.

**Features:**

- Multi-select port selection with checkboxes
- Controller selection
- Form validation
- Loading states
- Success/error handling

### DeleteBridgeDialog

Confirmation dialog for deleting bridges.

**Features:**

- Confirmation dialog using shadcn Alert Dialog
- Loading state during deletion (managed by parent component)
- Error handling
- Toast notifications
- Prevents accidental deletions
- Receives deletion state from parent component

## Usage

### Delete Bridge Flow

1. User clicks the trash icon on a bridge card
2. DeleteBridgeDialog opens with confirmation message
3. User confirms deletion
4. Loading overlay appears with spinner and "Deleting bridge..." text
5. Dialog content becomes non-interactive during deletion
6. API call is made to delete the bridge (managed by BridgeDataComponent)
7. Dialog closes only after API call completes (success or error)
8. Toast notification is shown on the page
9. Bridge data is refreshed

### API Integration

The delete functionality uses the existing `deleteBridge` function from `@/lib/devices`:

```tsx
export const deleteBridge = async (
  token: string,
  bridgeData: { name: string; lan_ip_address: string }
): Promise<unknown> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post("/delete-bridge/", bridgeData);
  return data;
};
```

## Styling

- Uses shadcn/ui components for consistent design
- Destructive styling for delete actions
- Responsive design
- Loading states with RingLoader
- Toast notifications using Sonner

## Error Handling

- Network errors are caught and displayed as toast notifications
- Loading states prevent multiple simultaneous operations
- Dialog prevents interaction during loading
- Graceful fallbacks for missing data
