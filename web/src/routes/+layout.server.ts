import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
const cookieLocale = cookies.get('agro_locale');
return {
locale: cookieLocale === 'en' || cookieLocale === 'es' ? cookieLocale : 'es'
};
};
