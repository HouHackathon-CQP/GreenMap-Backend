import httpx

from app.core.config import settings
from app import models


async def push_report_to_orion(report: models.UserReport):
    orion_url = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
    entity_id = f"urn:ngsi-ld:CivicIssue:Hanoi:{report.id}"

    payload = {
        "id": entity_id,
        "type": "CivicIssue",
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [report.longitude, report.latitude]},
        },
        "status": {"type": "Property", "value": "open"},
        "reportDate": {"type": "Property", "value": report.created_at},
        "name": {"type": "Property", "value": report.title},
        "@context": "https://schema.lab.fiware.org/ld/context",
    }

    if report.description:
        payload["description"] = {"type": "Property", "value": report.description}

    if report.image_url:
        payload["image"] = {"type": "Property", "value": report.image_url}

    headers = {"Content-Type": "application/ld+json"}

    async with httpx.AsyncClient() as client:
        response = await client.post(orion_url, json=payload, headers=headers)
        response.raise_for_status()
