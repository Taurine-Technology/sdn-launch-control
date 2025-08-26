# UI Components Documentation

## MultiSelect Component

The `MultiSelect` component provides a type-safe, production-ready multi-selection interface with checkboxes, similar to the Eventbrite audit report interface.

### Features

- ✅ Multiple selection with checkboxes
- ✅ Search functionality
- ✅ Select all/deselect all option
- ✅ Native mouse wheel scrolling (using shadcn ScrollArea)
- ✅ Keyboard navigation support
- ✅ Accessible design
- ✅ TypeScript support
- ✅ Customizable styling
- ✅ Badge display for selected items

### Usage

```tsx
import { MultiSelect, MultiSelectOption, MultiSelectBadges } from "@/components/ui/multi-select";

// Define your options
const options: MultiSelectOption[] = [
  { value: "port1", label: "Port 1" },
  { value: "port2", label: "Port 2" },
  { value: "port3", label: "Port 3" },
];

// In your component
const [selectedValues, setSelectedValues] = useState<string[]>([]);

const handleSelectionChange = (values: string[]) => {
  setSelectedValues(values);
};

const handleRemove = (value: string) => {
  setSelectedValues(selectedValues.filter(v => v !== value));
};

// Render the component
<MultiSelect
  options={options}
  selectedValues={selectedValues}
  onSelectionChange={handleSelectionChange}
  placeholder="Select ports"
  searchPlaceholder="Search ports..."
  emptyMessage="No ports available"
  disabled={false}
  maxDisplayed={3}
/>

// Display selected items as badges
<MultiSelectBadges
  selectedValues={selectedValues}
  options={options}
  onRemove={handleRemove}
/>
```

### Props

#### MultiSelect Props

| Prop                | Type                         | Default               | Description                               |
| ------------------- | ---------------------------- | --------------------- | ----------------------------------------- |
| `options`           | `MultiSelectOption[]`        | -                     | Array of selectable options               |
| `selectedValues`    | `string[]`                   | -                     | Currently selected values                 |
| `onSelectionChange` | `(values: string[]) => void` | -                     | Callback when selection changes           |
| `placeholder`       | `string`                     | `"Select options..."` | Placeholder text when nothing is selected |
| `searchPlaceholder` | `string`                     | `"Search options..."` | Placeholder for search input              |
| `emptyMessage`      | `string`                     | `"No options found."` | Message when no options match search      |
| `disabled`          | `boolean`                    | `false`               | Whether the component is disabled         |
| `className`         | `string`                     | -                     | Additional CSS classes                    |
| `maxDisplayed`      | `number`                     | `3`                   | Max number of items to display in trigger |

#### MultiSelectBadges Props

| Prop             | Type                      | Default | Description                      |
| ---------------- | ------------------------- | ------- | -------------------------------- |
| `selectedValues` | `string[]`                | -       | Currently selected values        |
| `options`        | `MultiSelectOption[]`     | -       | Array of all options             |
| `onRemove`       | `(value: string) => void` | -       | Callback when a badge is removed |
| `className`      | `string`                  | -       | Additional CSS classes           |

### MultiSelectOption Interface

```tsx
interface MultiSelectOption {
  value: string;
  label: string;
}
```

### Styling

The component uses Tailwind CSS classes and follows the shadcn/ui design system. It's fully customizable through the `className` prop and CSS variables.

### Accessibility

- Keyboard navigation support
- Native mouse wheel scrolling (no passive event listener issues)
- ARIA attributes for screen readers
- Focus management
- Proper semantic HTML structure

### Example Implementation

See `AddBridgeDialog.tsx` for a complete implementation example where the MultiSelect component is used for port selection in a bridge configuration dialog.

### Testing

Use `MultiSelectDemo` component to test the scrolling behavior with many options:

```tsx
import { MultiSelectDemo } from "@/components/ui/multi-select-demo";

// In your component
<MultiSelectDemo />;
```
