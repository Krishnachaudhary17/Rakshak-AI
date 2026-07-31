/* Shared Tailwind config + custom styles for all Rakshak AI pages */
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary-fixed": "#dae2fd", "outline-variant": "#45464d",
        "secondary-container": "#a40217", "surface-container-high": "#1c2b3c",
        "on-tertiary": "#472a00", "on-background": "#d4e4fa",
        "surface-variant": "#273647", "on-secondary": "#68000a",
        "on-surface-variant": "#c6c6cd", "on-secondary-container": "#ffaea8",
        "background": "#051424", "outline": "#909097",
        "on-tertiary-container": "#b47300", "surface-container-low": "#0d1c2d",
        "surface-bright": "#2c3a4c", "surface-container": "#122131",
        "surface-container-lowest": "#010f1f", "on-primary": "#283044",
        "surface-container-highest": "#273647", "surface-dim": "#051424",
        "tertiary": "#ffb95f", "error-container": "#93000a",
        "secondary": "#ffb3ad", "surface": "#051424",
        "primary-container": "#0f172a", "primary": "#bec6e0",
        "tertiary-container": "#251400", "error": "#ffb4ab",
        "inverse-on-surface": "#233143", "on-surface": "#d4e4fa",
        "on-primary-container": "#798098"
      },
      borderRadius: { "DEFAULT":"0.125rem","lg":"0.25rem","xl":"0.5rem","full":"0.75rem" },
      spacing: { "margin-mobile":"16px","base":"4px","margin-desktop":"32px","gutter":"16px","touch-target":"48px" },
      fontFamily: {
        "body-md":["Inter"],"display-lg-mobile":["Inter"],"display-lg":["Inter"],
        "headline-md":["Inter"],"body-lg":["Inter"],"headline-sm":["Inter"],
        "label-md":["JetBrains Mono"],"label-sm":["JetBrains Mono"]
      },
      fontSize: {
        "body-md":["16px",{"lineHeight":"24px","fontWeight":"400"}],
        "display-lg":["48px",{"lineHeight":"56px","letterSpacing":"-0.02em","fontWeight":"800"}],
        "headline-md":["24px",{"lineHeight":"32px","fontWeight":"700"}],
        "body-lg":["18px",{"lineHeight":"28px","fontWeight":"400"}],
        "headline-sm":["20px",{"lineHeight":"28px","fontWeight":"600"}],
        "label-md":["14px",{"lineHeight":"20px","letterSpacing":"0.05em","fontWeight":"500"}],
        "label-sm":["12px",{"lineHeight":"16px","letterSpacing":"0.05em","fontWeight":"500"}]
      }
    }
  }
};
