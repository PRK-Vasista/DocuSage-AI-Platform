// Button.jsx - Reusable button component for consistent styling and behavior.

import React from 'react';
// import './Button.css'; // Optional: for component-specific overrides

/**
 * A reusable button component that accepts styling props.
 *
 * @param {object} props
 * @param {string} [props.variant='primary'] - Controls the color scheme ('primary', 'secondary', 'red', 'link').
 * @param {string} [props.size='md'] - Controls padding and font size ('sm', 'md', 'lg').
 * @param {boolean} [props.fullWidth=false] - If true, makes the button span 100% width.
 * @param {boolean} [props.disabled=false] - Standard HTML disabled attribute.
 * @param {string} props.className - Additional custom CSS classes.
 * @param {React.Node} props.children - The content inside the button (text, icons).
 * @param {function} props.onClick - Click handler function.
 * @param {string} [props.type='button'] - Standard HTML type ('button', 'submit', 'reset').
 */
const Button = ({
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    disabled = false,
    className = '',
    children,
    onClick,
    type = 'button',
    ...rest
}) => {
    // Construct base classes using global styles (e.g., 'btn', 'btn-primary', 'btn-md')
    const baseClasses = `btn btn-${variant} btn-${size}`;
    const widthClass = fullWidth ? 'w-full' : '';

    // Combine classes
    const finalClasses = `${baseClasses} ${widthClass} ${className}`.trim();

    return (
        <button
            type={type}
            className={finalClasses}
            onClick={onClick}
            disabled={disabled}
            {...rest}
        >
            {children}
        </button>
    );
};

export default Button;
