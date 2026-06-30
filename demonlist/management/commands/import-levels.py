import asyncio
import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.core.management.base import BaseCommand
from demonlist.models import Level


class Command(BaseCommand):
    help = 'Асинхронный импорт уровней из Demonlist API'

    @sync_to_async
    def save_level(self, item_id, data):
        verification = data.get('verification') or {}
        level, created = Level.objects.update_or_create(
            level_id=item_id,
            defaults={
                'name': data.get('name') or 'Unknown',
                'global_demonlist_id': data.get('id'),
                'place': data.get('placement') or 0,
                'description': data.get('description') or '',
                'verifier': verification.get('username') or '',
                'video': verification.get('video_url') or '',
                'published': data.get('holder') or '',
                'creator': data.get('creator') or '',
                'thumbnail_url': f"https://thumbnails.demonlist.org/classic/{data.get('id')}.png" if data.get('id') else None,
            }
        )
        return created

    async def fetch_level_details(self, client, item, semaphore):
        async with semaphore:
            try:
                placement = item['placement']
                print(int(placement))

                url = f"https://api.demonlist.org/level/classic/get?placement={placement}"
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()

                level_data = response.json().get('data', [])

                # Вызываем обернутый метод сохранения
                created_flag = await self.save_level(item['ingame_id'], level_data)

                return 1 if created_flag else 0, 0 if created_flag else 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Ошибка уровня {item.get('name')}: {e}"))
                return 0, 0

    async def handle_async(self):
        list_url = 'https://api.demonlist.org/level/classic/list'

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(list_url)
                response.raise_for_status()
                data = response.json().get('data', {}).get('levels', [])
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Ошибка списка: {e}'))
                return

            levels_to_process = data[1320:]
            semaphore = asyncio.Semaphore(10)

            tasks = [
                self.fetch_level_details(client, item, semaphore)
                for item in levels_to_process
            ]

            results = await asyncio.gather(*tasks)

        created_count = sum(r[0] for r in results)
        updated_count = sum(r[1] for r in results)

        self.stdout.write(self.style.SUCCESS(f'Итог: добавлено {created_count}, обновлено {updated_count}'))

    def handle(self, *args, **options):
        async_to_sync(self.handle_async)()