declare module 'react-rainbow-components' {
  export function Card(props: {
    title?: string;
    actions?: React.ReactNode;
    loading?: boolean;
    children?: React.ReactNode;
    style?: React.CSSProperties;
  }): JSX.Element;

  export function Input(props: {
    label?: string;
    placeholder?: string;
    type?: string;
    value?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    maxLength?: number;
  }): JSX.Element;

  export function Button(props: {
    label?: string;
    variant?: 'brand' | 'success' | 'warning' | 'error' | 'destructive' | 'border' | 'base';
    size?: 'small' | 'medium' | 'large';
    loading?: boolean;
    onClick?: () => void;
    style?: React.CSSProperties;
  }): JSX.Element;

  export function Modal(props: {
    title?: string;
    isOpen?: boolean;
    onRequestClose?: () => void;
    children?: React.ReactNode;
  }): JSX.Element;

  export function ProgressBar(props: {
    value?: number;
    variant?: 'brand' | 'success' | 'warning' | 'error';
  }): JSX.Element;

  export function Badge(props: {
    label?: string;
    variant?: 'brand' | 'success' | 'warning' | 'error' | 'default' | 'destructive';
    style?: React.CSSProperties;
  }): JSX.Element;

  export function Avatar(props: {
    src?: string;
    initials?: string;
    size?: 'small' | 'medium' | 'large';
  }): JSX.Element;

  export function Spinner(props: { size?: 'small' | 'medium' | 'large' }): JSX.Element;

  export function Sidebar(props: { children?: React.ReactNode }): JSX.Element;
  export function SidebarItem(props: {
    label?: string;
    active?: boolean;
    onClick?: () => void;
  }): JSX.Element;

  export function Table<T>(props: {
    columns: Array<{
      header: string;
      field: string;
      component?: (props: { value: any; row: T }) => JSX.Element;
    }>;
    data: T[];
    keyField: string;
    pageSize?: number;
  }): JSX.Element;

  export function CounterInput(props: {
    label?: string;
    min?: number;
    max?: number;
    value?: number;
    onChange?: (value: number) => void;
  }): JSX.Element;

  export function DatePicker(props: {
    label?: string;
    value?: Date;
    onChange?: (value: Date) => void;
  }): JSX.Element;

  export function TimePicker(props: {
    label?: string;
    value?: Date;
    onChange?: (value: Date) => void;
  }): JSX.Element;

  export function Select(props: {
    label?: string;
    options?: Array<{ value: string; label: string }>;
    value?: string;
    onChange?: (value: string) => void;
  }): JSX.Element;

  export function CheckboxToggle(props: {
    label?: string;
    checked?: boolean;
    onChange?: (value: boolean) => void;
  }): JSX.Element;

  export function RainbowThemeContainer(props: { theme?: object; children?: React.ReactNode }): JSX.Element;
}