using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class EmitParticle : MonoBehaviour
{
    // Add this script to your ParticleSystem to let it emit particles
    public static ParticleSystem system;
    
    // These are the emission parameters (editable via script if you like)
    public static ParticleSystem.EmitParams settings = new ParticleSystem.EmitParams();
    
    // Start is called before the first frame update
    void Start()
    {
        // Set static variables now that we're created:
        EmitParticle.system=gameObject.GetComponent<ParticleSystem>();
    }
    
    /*
     Call:
        EmitParticle.Now(new Vector3(0,0,0), new Vector3(100,0,0), new Color(0,1,0,1), 20.0f);
     to emit one particle using these parameters:
        position: relative to the ParticleSystem (meters)
        velocity: relative to the ParticleSystem (m/s)
        color: initial color of particle (RGBA)
        emissionRate: number of particles to emit per second (on average, max 1 per frame)
    */
    public static void Now(Vector3 position, Vector3 velocity, Color color, float emissionRate=60.0f)
    {
        settings.position=position; // position relative to the particleSystem
        settings.velocity=velocity; // initial velocity
        settings.startColor=color; // RGBA
        
        bool emitWinner=(emissionRate*Time.deltaTime)>Random.Range(0.0f,1.0f); // lottery style
        if (system && emitWinner) 
            system.Emit(settings,1);
    }
    
    // Update is called once per frame
    void Update()
    {
        // Example of how to call us:
        // EmitParticle.Now(new Vector3(0,0,0), new Vector3(0,100,0), new Color(0,1,0,1), 20.0f);
    }
}
