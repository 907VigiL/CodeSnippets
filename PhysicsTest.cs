using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PhysicsTest : MonoBehaviour
{

    public Vector3 P;
    public Vector3 V;
    public Vector3 A;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        float deltaT = Time.deltaTime;
        V += A * deltaT;
        P += V * deltaT;
        transform.position = P;
    }
}
