import { Link } from 'react-router'                                                                                      
import { Button } from '@/components/ui/button'                                                                          
                                                                                                                        
                                                                                                                        
function NotFoundPage() {                                                                                                
    return (                                                                                                             
        <div className="page-centered">
            <h1 className="heading-display">404</h1>
            <p className="text-hero">Page not found</p>                                              
            <Button asChild variant="outline">                                                                           
                <Link to="/">Go home</Link>                                                                              
            </Button>                                                                                                    
        </div>                                                                                                           
    )                                                                                                                 
}

export default NotFoundPage