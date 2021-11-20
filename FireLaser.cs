using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FireLaser : MonoBehaviour
{

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        RaycastHit hit;
        if(!Physics.Raycast(transform.position, transform.right, out hit)) return;

        Collider c = hit.collider;
        GameObject obj = c.gameObject;
        MomentumSpinner mom = obj.GetComponent<MomentumSpinner>();
        if(mom)
        {
            Vector3 direction = transform.right;
            mom.ApplyTorque(hit.point, direction, Time.deltaTime);

            Vector3 flyDir = hit.normal;
            flyDir += Random.insideUnitSphere*0.5f;
            EmitParticle.Now(hit.point, flyDir*10.0f, new Color(1.0f, 1.0f, 1.0f, 1.0f));
        }
    }
}
