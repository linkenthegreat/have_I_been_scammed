# Frontend 🎨

Web interface for the Scam Prevention Tool with clean, modern design.

## Subdirectories
- `templates/`: Jinja2 HTML templates
- `static/`: CSS, JavaScript, and images

### Modules
- `templates/index.html`: Main UI page with:
  - Text/URL input tabs
  - **NEW**: Optional context gathering (location + role via collapsible section)
  - Risk assessment display (Safe/Caution/High badges)
  - **NEW**: Export buttons (Download PDF, Email Draft)
  - Feedback buttons
- `static/style.css`: Premium styling with Inter font, smooth animations
- `static/script.js`: Client-side logic for:
  - API calls to `/api/analyze`
  - Context submission (user_location, user_role)
  - Dynamic result display

## requirements
- Modern web browser with JavaScript enabled

## references
- Google Fonts (Inter): https://fonts.google.com/
- API Documentation: `back_end/README.md`
