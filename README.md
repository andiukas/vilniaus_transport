
<img width="710" height="439" alt="image" src="https://github.com/user-attachments/assets/e6e49197-50aa-480b-a106-c5f3c8d4e6fe" />


## Vilniaus viešojo transporto integracija

Ši integracija leidžia stebėti Vilniaus autobusų ir troleibusų judėjimą Home Assistant.  

**Įdiegimas:**
1. Įdiekite per **HACS** https://github.com/andiukas/vilniaus_transport/
2. Po įdiegimo pridėkite prie **Devices ant integrations**: Vilniaus viešasis transportas
3. Laukelye: **route** įrašote maršruto numerį pvz: 4G, 14 ir t.t.
4. Jei yra noras turėti kelis maršrutus 2 ir 3 punktus reikia pakartoti.
5. Pagal maršrutą automatiškai bus sukuriami `device_tracker` objektai.

**Pavyzdinė `Lovelace` kortelė:**

```yaml
type: custom:auto-entities
card:
  type: map
  title: "3G / 4G autobusai mieste"
  hours_to_show: 0
  dark_mode: false
filter:
  include:
    - entity_id: device_tracker.vln_4g_*
      options:
        name: "4G"
    - entity_id: device_tracker.vln_3g_*
      options:
        name: "3G"
show_empty: true
sort:
  method: friendly_name
