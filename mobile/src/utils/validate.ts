/**
 * Client-side image validation + backend error-code explanations.
 * Server-side validation (size/dimensions/format) is authoritative;
 * this only catches obvious problems early with useful messages.
 */

const ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'webp'];

export function validateLocalImage(uri: string | null | undefined): string | null {
  if (!uri) return 'No image selected. Take a photo or choose one from the gallery.';
  const clean = uri.split('?')[0].toLowerCase();
  const ext = clean.split('.').pop() ?? '';
  if (!ALLOWED_EXT.includes(ext)) {
    // Some gallery URIs lack extensions — warn, don't block: server decides.
    if (!clean.startsWith('content://') && !clean.startsWith('file://')) {
      return 'That file does not look like an image (JPG, PNG or WebP expected).';
    }
  }
  return null;
}

/** Friendly explanation for backend `{error:{code}}` values (codes verbatim). */
export function explainCode(code: string): string {
  switch (code) {
    case 'empty_image':
      return 'The uploaded file was empty.';
    case 'invalid_image':
      return 'The file could not be decoded as an image.';
    case 'unsupported_media':
      return 'Unsupported image type. Use JPG, PNG or WebP.';
    case 'image_too_large':
      return 'Image exceeds the 5 MB / 4000 px server limit. Try a smaller crop.';
    case 'image_too_small':
      return 'Image is smaller than 16 px — too small to read.';
    case 'model_unavailable':
      return 'The recognizer is not loaded (standby or still loading). Try again shortly.';
    case 'model_error':
      return 'The recognizer failed on this image. Try a clearer photo.';
    case 'empty_input':
    case 'parse_error':
    case 'bad_token':
    case 'unknown_variable':
      return 'The expression uses syntax outside the v1 grammar (numbers, + - * / ^, parens, sqrt(), variables x y z t). Edit it and retry.';
    case 'unsupported_syntax':
      return 'That LaTeX or syntax is not supported yet (e.g. functions beyond sqrt(), subscripts, matrices). Simplify the expression.';
    case 'unbound_variable':
      return 'The expression still has a variable without a value — enter values or use Simplify/Solve.';
    case 'division_by_zero':
      return 'Division by zero is not allowed.';
    case 'solve_failed':
      return 'No verifiable solution found for that equation.';
    case 'complex_result':
      return 'Complex-valued results are not supported in v1.';
    case 'too_complex':
    case 'input_too_long':
      return 'Expression exceeds v1 size limits. Shorten it and retry.';
    case 'unreachable':
      return 'Backend unreachable. Check the API URL and that the server is running.';
    case 'timeout':
      return 'The request timed out — nothing was lost. Try again.';
    default:
      return 'Request failed — nothing was lost. Try again.';
  }
}
